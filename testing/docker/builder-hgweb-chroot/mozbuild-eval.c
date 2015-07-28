/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/* This program is used to chroot into a secure execution environment
 * for evaluating moz.build files.
 *
 * It attempts to follow many of the best practices described at
 * http://www.unixwiz.net/techtips/chroot-practices.html.
 */

/* To get setresuid() */
#define _GNU_SOURCE

#include <grp.h>
#include <mntent.h>
#include <pwd.h>
#include <sched.h>
#include <stdio.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include <libcgroup.h>

#define CHROOT "/repo/hg/chroot_mozbuild"

/* environment for process executed in chroot */
const char* chroot_env[] = {
    "HOME=/",
    "PATH=/usr/bin;/bin",
    "HGENCODING=utf-8",
    NULL,
};

const char* hostname = "mozbuildeval";

static char stack[1048576];

/**
 * Child process that does all the work. This process is disassociated
 * from the parent. But it still has root privileges.
 */
static int call_mozbuildinfo(void* repo_path) {
    struct passwd* user = NULL;
    FILE* fmount;
    struct mntent* mnt;
    int err = -1;
    struct cgroup* cg;
    pid_t pid;
    int child_status;

    /* We have a new UTS namespace, so set a hostname. */
    if (sethostname(hostname, strlen(hostname))) {
        fprintf(stderr, "unable to set hostname in child\n");
        return 1;
    }

    user = getpwnam("mozbuild");
    if (!user) {
        fprintf(stderr, "mozbuild user not found\n");
        return 1;
    }

    /* While we have a cgrules rule in place to ensure all processes
     * belonging to the mozbuild user are placed in the mozbuild control
     * group, documentation indicates there may be a lag between when
     * the process is created and/or when the uid of the process
     * changes. We practice defense in depth and explicitly attach to
     * the desired control group. */
    cgroup_init();
    cg = cgroup_new_cgroup("mozbuild");
    if (!cg) {
        fprintf(stderr, "unable to obtain mozbuild cgroup\n");
        return 1;
    }
    /* The created cgroup reference is empty by default. We need to
     * reconcile it with the system state by calling cgroup_get_cgroup()
     * so cgroup_attach_task() knows which controllers to modify. */
    if (cgroup_get_cgroup(cg)) {
        fprintf(stderr, "unable to obtain cgroup info\n");
        return 1;
    }
    if (cgroup_attach_task(cg)) {
        fprintf(stderr, "unable to attach process to cgroup\n");
        return 1;
    }
    cgroup_free(&cg);

    /* We have a separate mount namespace from the parent but we
     * inherited a copy. Clear out mounts because they only increase the
     * surface area for badness. */
    fmount = setmntent("/proc/mounts", "r");
    if (!fmount) {
        fprintf(stderr, "unable to open /proc/mounts\n");
        return 1;
    }

    while ((mnt = getmntent(fmount))) {
        /* These can't be deleted during our first pass because there
         * are child mounts. */
        if (strcmp(mnt->mnt_dir, "/dev") == 0) {
            continue;
        }
        if (strcmp(mnt->mnt_dir, "/proc") == 0) {
            continue;
        }
        /* We need the root filesystem and the repo bind mount available
         * in order for the chroot to work. */
        if (strcmp(mnt->mnt_dir, "/") == 0) {
            continue;
        }
        if (strcmp(mnt->mnt_dir, "/repo_local/mozilla/chroot_mozbuild/repo/hg/mozilla") == 0) {
            continue;
        }

        if (umount2(mnt->mnt_dir, 0)) {
            fprintf(stderr, "unable to unmount %s\n", mnt->mnt_dir);
            endmntent(fmount);
            return 1;
        }
    }

    /* Always returns 1. */
    endmntent(fmount);

    /* Now unmount /dev and /proc since children should be gone. */
    if (umount2("/dev", 0)) {
        fprintf(stderr, "unable to unmount /dev\n");
        return 1;
    }

    /* It is especially important that proc is unmounted because
     * historically there have been a lot of root privilege escalation
     * bugs in procfs. */
    if (umount2("/proc", 0)) {
        fprintf(stderr, "unable to unmount /proc\n");
        return 1;
    }

    /* chdir() and chroot() go hand in hand. Otherwise child process can
     * get handle for things outside the chroot. */
    err = chdir(CHROOT);
    if (err) {
        fprintf(stderr, "unable to chdir: %d\n", err);
        return 1;
    }

    err = chroot(CHROOT);
    if (err) {
        fprintf(stderr, "unable to chroot\n");
        return 1;
    }

    /* Change to mozbuild user/group.
     * We use setres[ug]id() because it sets real, effective, and saved in
     * one go */
    err = setresgid(user->pw_gid, user->pw_gid, user->pw_gid);
    if (err) {
        fprintf(stderr, "unable to setresgid\n");
        return 1;
    }

    if (setgroups(0, NULL)) {
      fprintf(stderr, "unable to set supplementary groups\n");
      return 1;
    }

    err = setresuid(user->pw_uid, user->pw_uid, user->pw_uid);
    if (err) {
        fprintf(stderr, "unable to setresuid\n");
        return 1;
    }

    /* And now that we've dropped all privileges, do our moz.build
     * evaluation. Since we are in a PID namespace and we are PID 1, we
     * do a fork first because PID 1 is special and we don't want our
     * Python process possibly getting tangled in those properties. */
    pid = fork();
    if (pid == -1) {
        fprintf(stderr, "unable to fork\n");
        return 1;
    }
    if (pid == 0) {
      execle("/usr/bin/python", "/usr/bin/python", "/usr/bin/hg",
                 /* repository paths inside and outside chroot are the same */
                 "-R", (char*)repo_path,
                 /* hgmo extension provides mozbuildinfo command */
                 "--config", "extensions.hgmo=/repo/hg/version-control-tools/hgext/hgmo",
                 /* --pipemode pulls arguments from JSON over stdin */
                 "mozbuildinfo", "--pipemode",
                 NULL,
                 chroot_env);
      _exit(1);
    } else {
      if (waitpid(pid, &child_status, 0) == -1) {
          fprintf(stderr, "failed to wait on Python process\n");
          return 1;
      }

      if (!WIFEXITED(child_status)) {
          fprintf(stderr, "Python process did not terminate normally\n");
          return 1;
      }

      return WEXITSTATUS(child_status);
    }
}

int main(int argc, const char* argv[]) {
    int fd, fd_count;
    pid_t pid;
    int clone_flags, child_status;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s /path/to/repo\n", argv[0]);
        return 1;
    }

    /* Close all non-standard file descriptors before the clone because
     * they aren't needed. */
    fd_count = getdtablesize();
    if (fd_count == -1) {
        fd_count = sysconf(_SC_OPEN_MAX);
    }
    for (fd = 3; fd < fd_count; fd++) {
        close(fd);
    }

    /* TODO use CLONE_USER once we run on a modern kernel (not CentOS * 6). */
    clone_flags =
        /* Send signal to parent when child dies. */
        SIGCHLD |
        /* Share file descriptors. */
        CLONE_FILES |
        /* Create a new IPC namespace for the child. We want the child
         * to be isolated from us for security reasons. */
        CLONE_NEWIPC |
        /* Create a new network namespace for the child. */
        CLONE_NEWNET |
        /* Create a new mount namespace for the child. */
        CLONE_NEWNS |
        /* Create a new PID namespace for the child. */
        CLONE_NEWPID |
        /* Create a new UTS namespace for the child. */
        CLONE_NEWUTS;

    pid = clone(call_mozbuildinfo,
                stack + sizeof(stack),
                clone_flags,
                (void*)argv[1]);
    if (pid < 1) {
        fprintf(stderr, "clone failed\n");
        return 1;
    }

    if (waitpid(pid, &child_status, 0) == -1) {
        fprintf(stderr, "failed to wait on child\n");
        return 1;
    }

    if (WIFEXITED(child_status)) {
        return WEXITSTATUS(child_status);
    }

    fprintf(stderr, "child did not terminate normally\n");

    /* We should never get here. But the compiler isn't that smart. */
    return 1;
}
