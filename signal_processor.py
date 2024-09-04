from scipy.signal import lfilter, firwin, decimate
from scipy import signal
import matplotlib.pyplot as plt
from pydub import AudioSegment
import numpy


class SignalProcessor:
    """
    SignalProcessor class for processing signals.
    Args:
        plotNames (list): List of plot names. Index 1 is the name of the plot for the first plot samp_by_amp_demod default name and 2 is waterfall_demod.
    """

    def __init__(self, plotNames=["sba_pre_save_demod", "w_demod"]):
        self.plotNames = plotNames

    def fm_demodulate(
        self,
        fm_samples,
        squelch: float,
        fs: float | int = 250e3,
        df: float = 1.0,
        fc: float = 0.0,
    ):
        """Perform FM demodulation of complex carrier.

        Args:
            x (array):  FM modulated complex carrier.
            fs (float): Sampling frequency [Hz].
            df (float): Normalized frequency deviation [Hz/V].
            fc (float): Normalized carrier frequency.

        Returns:
            Array of real modulating signal.
        """
        print("Demodulating " + str(len(fm_samples)) + " samples...")
        self.plot_waterfall(
            fm_samples,
            fs,
            "waterfall_rawiq",
            "Waterfall Plot of Raw IQ Data",
            "Time (s)",
            "Frequency (Hz)",
        )

        # Filter high noise out of the signal before demodulating
        b, a = signal.butter(2, 3e3, "lowpass", fs=fs)
        fm_samples = signal.lfilter(b, a, fm_samples)

        # Negate samples below squelch threshold and above clip threshold which is 0.8 for this example
        # fm_samples = numpy.where(numpy.abs(fm_samples) < 0.8, fm_samples, 0)
        fm_samples = numpy.where(numpy.abs(fm_samples) > squelch, fm_samples, 0)

        # Remove carrier.
        n = numpy.arange(len(fm_samples))
        rx = fm_samples * numpy.exp(-1j * 2 * numpy.pi * fc * n)

        # Extract phase of carrier.
        phi = numpy.arctan2(numpy.imag(rx), numpy.real(rx))

        # Calculate frequency from phase.
        demod = numpy.diff(numpy.unwrap(phi) / (2 * numpy.pi * df))

        self.plot_waterfall(
            demod,
            fs,
            "waterfall_demodulated",
            "Waterfall Plot of Demodulated Signal\nPost Lowpass",
            "Time (s)",
            "Frequency (Hz)",
        )

        # Do our filtering -------------------------------------

        demod = self.bandpass_voice(demod, fs)

        # Normalize the signal to the range of -1 to 1
        demod = self.normailize_signal(demod)

        self.plot_waterfall(
            demod,
            fs,
            "waterfall_demodulated_filtered",
            "Waterfall Plot of Demodulated Signal\nDone Demodulating",
            "Time (s)",
            "Frequency (Hz)",
        )

        return demod

    def normailize_signal(self, samples: numpy.ndarray):
        """
        Normalize the given signal to the range of -1 to 1.

        Parameters:
        - samples (numpy.ndarray): The input signal.

        Returns:
        - numpy.ndarray: The normalized signal.

        """
        # Normalize the signal to the range of -1 to 1
        samples /= numpy.max(numpy.abs(samples))

        return samples

    def bandpass_voice(self, samples: numpy.ndarray, fs: float | int):
        """
        Applies a band-pass filter to the given audio samples to remove out of perception noise.
        Parameters:
        - samples (numpy.ndarray): The input audio samples.
        - fs (float | int): The sampling rate of the audio.
        Returns:
        - numpy.ndarray: The filtered audio samples.
        """

        # Design a band-pass filter
        nyquist_rate = 0.5 * fs
        low_cutoff = 300  # Low cutoff frequency in Hz
        high_cutoff = 3000  # High cutoff frequency in Hz
        numtaps = 1024  # Number of filter taps

        # Normalize the cutoff frequencies
        low = low_cutoff / nyquist_rate
        high = high_cutoff / nyquist_rate

        # Create a band-pass filter
        bandpass_filter = firwin(numtaps, [low, high], pass_zero=False)

        # Apply the band-pass filter to the signal
        samples = lfilter(bandpass_filter, 1, samples)

        return samples

    def float32_to_int16(self, float_array):
        """
        Converts an array of float32 values to int16.

        Parameters:
        - float_array (ndarray): Array of float32 values.

        Returns:
        - int16_array (ndarray): Array of int16 values.

        """
        # Ensure the values are within the range -1.0 to 1.0
        float_array = numpy.clip(float_array, -1.0, 1.0)
        # Scale the values to the range of int16
        int16_array = (float_array * 32767).astype(numpy.int16)
        return int16_array

    def decimate_samples(self, from_rate, to_rate, samples):
        """
        Decimates the given signal from one sampling rate to another.

        Parameters:
        - from_rate (float): The original sampling rate of the signal.
        - to_rate (float): The desired sampling rate of the decimated signal.
        - samples (ndarray): The signal samples to be decimated.

        Returns:
        - decimated_signal (ndarray): The decimated signal.

        """
        decimated_signal = decimate(samples, int(from_rate / to_rate))

        # Smooth the decimated signal
        # decimated_signal = decimated_signal - numpy.mean(decimated_signal)

        return decimated_signal

    def save_numpy_as_mp3(
        self, sample_rate: int, int_samples: numpy.ndarray, output_name: str
    ):
        """
        Save the given numpy array of samples as an mp3 audio file.
        Parameters:
        - sample_rate (int): The sample rate of the audio.
        - int_samples (numpy.ndarray): The numpy array of samples.
        - output_name (str): The name of the output file.
        """

        # Convert numpy array to AudioSegment
        audio_segment = AudioSegment(
            int_samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=int_samples.dtype.itemsize,
            channels=1,
        )

        try:
            # Export as MP3
            audio_segment.export(output_name, format="mp3")
        except FileNotFoundError as e:
            print(
                "Error!! This one indicates you likely do not have ffmpeg installed you goober!: ",
                e,
            )
            exit(1)
        pass

    def run_plots(self, samples, rate):
        """
        Run plots for the given samples and rate.

        Parameters:
        - samples: The signal samples to be plotted.
        - rate: The sampling rate of the signal.

        Returns:
        None
        """
        self.plot_signal(samples)
        self.plot_waterfall(samples, rate)

    def plot_signal(
        self,
        samples,
        fileName=None,
        title="Demodulated Signal",
        xlabel="Sample Index",
        ylabel="Amplitude",
    ):
        """
        Plots the given signal samples.
        Parameters:
            samples (list): The signal samples to be plotted.
            fileName (str, optional): The name of the file to save the plot. If not provided, a default name will be used.
            title (str, optional): The title of the plot. Defaults to "Demodulated Signal".
            xlabel (str, optional): The label for the x-axis. Defaults to "Sample Index".
            ylabel (str, optional): The label for the y-axis. Defaults to "Amplitude".
        """
        if fileName is None:
            fileName = self.plotNames[0]

        print(f"Running signal plot... ({fileName})")

        plt.figure()
        plt.plot(samples)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.savefig("charts/" + fileName + ".png")
        plt.close()

    def plot_waterfall(
        self,
        samples,
        rate,
        fileName=None,
        title="Waterfall Plot",
        xlabel="Time (s)",
        ylabel="Frequency (Hz)",
    ):
        """
        Plot a waterfall plot.
        Parameters:
        - samples: array-like
            The input signal samples.
        - rate: int or float
            The sample rate of the input signal.
        - fileName: str, optional
            The name of the output file. If not provided, a default name will be used.
        - title: str, optional
            The title of the plot. Default is "Waterfall Plot".
        - xlabel: str, optional
            The label for the x-axis. Default is "Time (s)".
        - ylabel: str, optional
            The label for the y-axis. Default is "Frequency (Hz)".
        """

        if fileName is None:
            fileName = self.plotNames[1]

        print(f"Running waterfall plot... ({fileName})")

        # Prevent division by 0
        samples += 1e-10

        numpy.seterr(divide="ignore")
        plt.figure()
        plt.specgram(samples, NFFT=1024, Fs=rate, noverlap=512)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.savefig("charts/" + fileName + ".png")
        plt.close()
        numpy.seterr(divide="warn")

    def basicPlot(self, array, fileName):
        """
        Plots the given array and saves the plot as an image file.

        Parameters:
        - array: The array to be plotted.
        - fileName: The name of the file to save the plot as.

        Returns:
        None
        """
        plt.plot(array)
        plt.savefig("charts/{0}.png".format(fileName))
