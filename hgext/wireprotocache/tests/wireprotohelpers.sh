HTTPV2=exp-http-v2-0003
MEDIATYPE=application/mercurial-exp-framing-0006

sendhttpraw() {
  hg --verbose debugwireproto --peer raw http://$LOCALIP:$HGPORT/
}

sendhttpv2peer() {
  hg --config experimental.httppeer.v2-encoder-order=identity debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/
}

sendhttpv2peerverbose() {
  hg --config experimental.httppeer.v2-encoder-order=identity --verbose debugwireproto --nologhandshake --peer http2 http://$LOCALIP:$HGPORT/
}

sendhttpv2peerhandshake() {
  hg --config experimental.httppeer.v2-encoder-order=identity --verbose debugwireproto --peer http2 http://$LOCALIP:$HGPORT/
}

cat > dummycommands.py << EOF
from mercurial import (
    wireprototypes,
    wireprotov1server,
    wireprotov2server,
)

@wireprotov1server.wireprotocommand(b'customreadonly', permission=b'pull')
def customreadonlyv1(repo, proto):
    return wireprototypes.bytesresponse(b'customreadonly bytes response')

@wireprotov2server.wireprotocommand(b'customreadonly', permission=b'pull')
def customreadonlyv2(repo, proto):
    yield b'customreadonly bytes response'

@wireprotov1server.wireprotocommand(b'customreadwrite', permission=b'push')
def customreadwrite(repo, proto):
    return wireprototypes.bytesresponse(b'customreadwrite bytes response')

@wireprotov2server.wireprotocommand(b'customreadwrite', permission=b'push')
def customreadwritev2(repo, proto):
    yield b'customreadwrite bytes response'
EOF

enabledummycommands() {
  cat >> $HGRCPATH << EOF
[extensions]
dummycommands = $TESTTMP/dummycommands.py
EOF
}

enablehttpv2() {
  cat >> $1/.hg/hgrc << EOF
[experimental]
web.apiserver = true
web.api.http-v2 = true
EOF
}

enablehttpv2client() {
  cat >> $HGRCPATH << EOF
[experimental]
httppeer.advertise-v2 = true
# So tests are in plain text. Also, zstd isn't available in all installs,
# which would make tests non-deterministic.
httppeer.v2-encoder-order = identity
EOF
}
