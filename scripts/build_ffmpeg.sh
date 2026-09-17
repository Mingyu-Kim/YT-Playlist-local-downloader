#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="$ROOT/.vendor/audio-prefix"
mkdir -p "$PREFIX" "$ROOT/tools" "$ROOT/build/licenses/ffmpeg" "$ROOT/build/licenses/lame"
JOBS="${JOBS:-4}"
export CFLAGS="${CFLAGS:-} -O2"
if [ "$(uname -s)" = "Windows_NT" ]; then export PATH_SEPARATOR=";" CC=gcc.exe AWK=awk.exe AR=ar.exe RANLIB=ranlib.exe NM=nm.exe STRIP=strip.exe; fi
HOST_ARGS=
FFMPEG_TARGET=
case "$(uname -s)" in
  MINGW*|MSYS*|Windows_NT) export LDFLAGS="${LDFLAGS:-} -static"; SUFFIX=.exe; HOST_ARGS="--build=x86_64-w64-mingw32 --host=x86_64-w64-mingw32"; FFMPEG_TARGET="--target-os=mingw32" ;;
  Darwin) SUFFIX=; case "$(uname -m)" in arm64) HOST_ARGS="--build=aarch64-apple-darwin --host=aarch64-apple-darwin" ;; esac ;;
  *) SUFFIX= ;;
esac
cd "$ROOT/.vendor/lame-3.100"
sh ./configure $HOST_ARGS --prefix="$PREFIX" --disable-shared --enable-static --disable-frontend --disable-dependency-tracking
make SHELL=sh -j"$JOBS"
make SHELL=sh install
cd "$ROOT/.vendor/ffmpeg-7.1.2"
sh ./configure $FFMPEG_TARGET --prefix="$PREFIX" --disable-autodetect --disable-network --disable-doc --disable-debug   --disable-ffplay --disable-ffprobe --disable-shared --enable-static --disable-x86asm   --disable-everything --enable-ffmpeg --enable-avfilter --enable-swresample   --enable-protocol=file,pipe --enable-demuxer=mov,matroska,ogg,mp3,flac,wav,aac   --enable-decoder=aac,aac_fixed,opus,vorbis,mp3,mp3float,flac,pcm_s16le,pcm_s24le,pcm_s32le,pcm_f32le   --enable-parser=aac,mpegaudio,opus,vorbis,flac --enable-encoder=libmp3lame   --enable-muxer=mp3 --enable-filter=aresample,aformat,anull,sine --enable-indev=lavfi   --enable-libmp3lame --extra-cflags="-I$PREFIX/include" --extra-ldflags="-L$PREFIX/lib ${LDFLAGS:-}"
make SHELL=sh -j"$JOBS"
cp "ffmpeg$SUFFIX" "$ROOT/tools/ffmpeg$SUFFIX"
cp COPYING.LGPLv2.1 LICENSE.md "$ROOT/build/licenses/ffmpeg/"
cp "$ROOT/.vendor/lame-3.100/COPYING" "$ROOT/build/licenses/lame/"
"$ROOT/tools/ffmpeg$SUFFIX" -version > "$ROOT/tools/ffmpeg-build.txt"
printf '\nBuilt from sources pinned in scripts/tools.lock.json with scripts/build_ffmpeg.sh\n' >> "$ROOT/tools/ffmpeg-build.txt"
