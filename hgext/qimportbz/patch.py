# Parses a patch into message, user, date, diff
# Based on mq.py
def parse(data):
  user = ''
  date = ''
  msg = []
  subject = ''
  format = None
  diffstart = 0
  lines = data.splitlines()
  for i,line in enumerate(lines):
    line = line.rstrip()
    if line.startswith('diff ') or line.startswith('--- ') or \
       line.startswith('+++ ') or line.startswith("Index: "):
      diffstart = i
      break
    if line == '# HG changeset patch':
      format = 'hgpatch'
    elif format == 'hgpatch':
      if line.startswith("# User "):
        user = line[7:]
      elif line.startswith("# Date "):
        date = line[7:]
      elif not line.startswith("# ") and line:
        msg.append(line)
        format = None
    elif format != "tagdone" and line.lower().startswith("subject: "):
      subject = line[9:]
      format = "tag"
    elif format != "tagdone" and line.lower().startswith("from: "):
      user = line[6:]
      format = "tag"
    elif format == "tag" and line == "":
      format = "tagdone"
    elif msg or line:
      msg.append(line)

  if format and format.startswith("tag") and subject:
    message.insert(0, '')
    message.insert(0, subject)

  diff = '\n'.join(lines[diffstart:])+'\n'
  return ('\n'.join(msg), user, date, diff)

