from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
from signal_processor import SignalProcessor
from scipy.io.wavfile import write

sample_rate = int(250e3)
output_sample_rate = int(6e3)

# Load the samples from the file
def get_samples():
    samps = np.fromfile("output/iq_samples.npy", dtype=np.complex64)
    return samps

# Demodulate the samples
sp = SignalProcessor()

iq_samples = get_samples()

# Plot the samples in a heatmap
plt.title("Waterfall of Samples")
plt.ylabel("Frequency (Hz)")
plt.xlabel("Time (s)")
plt.specgram(iq_samples, NFFT=1024, Fs=sample_rate, noverlap=900)
plt.show()

# Create a highpass and lowpass with scipy to discard +3kHz
b, a = signal.butter(2, 3e3, 'lowpass', fs=sample_rate)
iq_samples = signal.lfilter(b, a, iq_samples)

plt.title("Waterfall of Filtered Samples")
plt.ylabel("Frequency (Hz)")
plt.xlabel("Time (s)")
plt.specgram(iq_samples, NFFT=1024, Fs=sample_rate, noverlap=900)
plt.show()

# Negate samples below squelch threshold and above clip threshold which is 0.8 for this example
squelch_threshold = 0.2
iq_samples = np.where(np.abs(iq_samples) < 0.8, iq_samples, 0)
iq_samples = np.where(np.abs(iq_samples) > squelch_threshold, iq_samples, 0)

# Plot the average power level of every sample
meanLevels = []
for i in range(0, len(iq_samples), 1024):
    meanLevels.append(np.abs(iq_samples[i:i+1024]).mean())

plt.title("Mean Power Levels")
plt.ylabel("Mean Power Level")
plt.xlabel("Sample Index")
plt.plot(meanLevels)
plt.show()

demod = sp.fm_demodulate(iq_samples, 0.3)

# Make a plot of demodulated samples
plt.title("Demodulated Samples")
plt.ylabel("Amplitude")
plt.xlabel("Sample Index")
plt.plot(demod)
plt.show()

# Cut +- 0.4 amplitude off the demodulated samples
demod = np.where(demod > 0.4, 0.4, demod)
demod = np.where(demod < -0.4, -0.4, demod)

demodulated_resamped = sp.decimate_samples(
    sample_rate, 
    output_sample_rate, 
    demod
)

# Plot demodulated_resampled samples with time axis
plt.title("Demodulated Samples Resampled")
plt.ylabel("Amplitude")
plt.xlabel("Sample Index")
plt.plot(demodulated_resamped)
plt.show()

write("output/demodulated.wav", output_sample_rate, demodulated_resamped.astype(np.float32))