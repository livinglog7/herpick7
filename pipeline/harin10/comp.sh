# usage: comp.sh slot voiceidx bgmoffset "hook" "sub"   (source: ~/mv7/n<slot>.mp4, voice: v<idx>.mp3)
set -e; s=$1; vi=$2; off=$3; cd ~/v10
~/venv/bin/python mk.py "$4" "$5" 2>/dev/null || python3 mk.py "$4" "$5"
mv hook.png hook_$s.png; mv sub.png sub_$s.png
src=~/mv7/n$s.mp4
vd=$(ffprobe -v 0 -show_entries format=duration -of csv=p=0 v$vi.mp3)
ve=$(python3 -c "print(round(0.8+$vd+0.3,2))")
ffmpeg -nostdin -y -v error -i $src -filter_complex "[0:v]fps=30,split[f][r0];[r0]reverse,trim=start_frame=1,setpts=PTS-STARTPTS[r];[f][r]concat=n=2:v=1[c]" -map "[c]" -c:v libx264 -crf 16 -preset fast -an loop_$s.mp4 </dev/null
D=$(ffprobe -v 0 -show_entries format=duration -of csv=p=0 loop_$s.mp4)
st=$(python3 -c "print($D-1.0)")
ffmpeg -nostdin -y -v error -i loop_$s.mp4 -ss $off -i ~/bgm/chill.m4a -i v$vi.mp3 -loop 1 -i hook_$s.png -loop 1 -i sub_$s.png -filter_complex "\
[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.08[bg];[b]scale=1080:1440[fg];[bg][fg]overlay=0:240[v1];\
[v1][3:v]overlay=0:0:shortest=1[v2];[v2][4:v]overlay=0:1680:enable='between(t,0.7,$ve)':shortest=1,format=yuv420p[v];\
[1:a]atrim=0:$D,asetpts=PTS-STARTPTS,loudnorm=I=-22,afade=t=in:d=0.4,afade=t=out:st=$st:d=1.0[m];\
[2:a]loudnorm=I=-15,adelay=800|800,apad[vo];[m][vo]amix=inputs=2:duration=first:normalize=0[aud]" \
-map "[v]" -map "[aud]" -t $D -c:v libx264 -crf 19 -preset medium -r 30 -c:a aac -b:a 160k -movflags +faststart h10_$s.mp4 </dev/null
echo $s $(ffprobe -v 0 -show_entries format=duration -of csv=p=0 h10_$s.mp4) $(ffprobe -v 0 -select_streams a -show_entries stream=duration -of csv=p=0 h10_$s.mp4)
