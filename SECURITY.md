# 🔒 Security

Only the latest release is maintained. Security fixes are not backported unless explicitly stated.

Report sensitive vulnerabilities with GitHub **Security → Report a vulnerability** when private reporting is enabled. If unavailable, open an issue requesting a private contact without including exploit details, credentials or personal files. Do not post tokens, cookies or private music-library data publicly.

Scope includes loopback authentication, Host/Origin validation, path handling, archive extraction, bundled tools and release supply-chain integrity. The app should never bind to a non-loopback interface. No remote API is supported.

Distributors should keep bundled yt-dlp, Node, FFmpeg and dependencies current, run all native checks, and review dependency licenses. Releases are currently unsigned; signing and Apple notarization are not claimed.
