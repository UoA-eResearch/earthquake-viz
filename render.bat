ffmpeg -framerate 24 -i %1/frame.%%04d.png -c:v libx264 -pix_fmt yuv420p %1.mp4