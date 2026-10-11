#!/usr/bin/env bash
# Synthesises the four subtle UI sound effects with ffmpeg (no third-party samples,
# so there is nothing to license). Re-run to regenerate; replace the files freely.
set -euo pipefail
cd "$(dirname "$0")/../public/audio/sfx"
FF="ffmpeg -hide_banner -loglevel error -y"

# Light click — a very short, high, quickly decaying tick.
$FF -f lavfi -i "sine=f=2300:d=0.05:sample_rate=48000" \
  -af "afade=t=out:st=0:d=0.05:curve=exp,volume=0.5" -ac 2 click.wav

# Thin line being drawn — airy filtered noise that swells and fades.
$FF -f lavfi -i "anoisesrc=d=0.7:c=pink:a=0.5:r=48000" \
  -af "highpass=f=2500,lowpass=f=9000,afade=t=in:st=0:d=0.25,afade=t=out:st=0.3:d=0.4,volume=0.35" -ac 2 line.wav

# Low impact — a soft sub thump with a long exponential tail.
$FF -f lavfi -i "sine=f=48:d=1.2:sample_rate=48000" -f lavfi -i "anoisesrc=d=0.08:c=brown:a=0.6:r=48000" \
  -filter_complex "[0]afade=t=out:st=0:d=1.2:curve=exp[a];[1]lowpass=f=300,afade=t=out:st=0:d=0.08[b];[a][b]amix=inputs=2:normalize=0,volume=0.9" -ac 2 impact.wav

# Restrained slide — band-passed noise with a gentle rise and fall.
$FF -f lavfi -i "anoisesrc=d=0.6:c=pink:a=0.5:r=48000" \
  -af "bandpass=f=900:width_type=o:w=1.5,afade=t=in:st=0:d=0.3:curve=qsin,afade=t=out:st=0.3:d=0.3:curve=qsin,volume=0.6" -ac 2 slide.wav

ls -la
