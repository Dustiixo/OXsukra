# VELA M2.30 — A/B playback position marker

One change: the existing native A/B waveform now draws a read-only playback cursor updated approximately every 40 ms from the isolated BarAudition frame counter. The marker is clamped to the plotted interval and stops scheduling when the window closes. No audio samples, transport, FID format, approval state, or original media are changed.

The cursor follows frames rendered by the audio callback, not measured DAC output latency. Hardware latency and Windows playback remain unverified.
