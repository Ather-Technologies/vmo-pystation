import os
import numpy
from rtlsdr import RtlSdr, RtlSdrAio
from typing import NamedTuple
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)  # take environment variables from .env.


class StationController:
    class Config(NamedTuple):
        """
        Represents the configuration type for a station.
        """

        def toString(self) -> str:
            """
            Returns a string representation of the station controller's attributes.

            Returns:
                str: A string containing the values of the following attributes:
                    - VFO_FS
                    - VFO_CTR_FREQ
                    - VFO_GAIN
                    - OUT_FILE_FS
                    - UPLOAD_ENDPOINT
                    - STATION_SRC_ID
                    - SQUELCH
                    - WAIT_TO_END
                    - DEBUG_MODE
            """
            return f"VFO_FS={self.VFO_FS},\nVFO_CTR_FREQ={self.VFO_CTR_FREQ},\nVFO_GAIN={self.VFO_GAIN}=OUT_FILE_FS={self.OUT_FILE_FS},\nUPLOAD_ENDPOINT={self.UPLOAD_ENDPOINT},\nSTATION_SRC_ID={self.STATION_SRC_ID},\nSQUELCH={self.SQUELCH},\nWAIT_TO_END={self.WAIT_TO_END},\nDEBUG_MODE={self.DEBUG_MODE}"

        VFO_FS: int
        """Radio sample rate in Hz."""
        VFO_CTR_FREQ: int
        """Radio center freq in Hz."""
        VFO_GAIN: str | int
        """Radio gain in dB or "auto"/None for auto gain."""
        OUT_FILE_FS: int
        """Output sample rate in Hz."""
        UPLOAD_ENDPOINT: str
        """API URL to upload the demodulated audio to."""
        STATION_SRC_ID: int
        """Station source ID"""
        SQUELCH: float
        """Alter this to avoid squelch tripping on static"""
        WAIT_TO_END: int
        """Wait for 5 seconds of quiet before ending recording"""
        DEBUG_MODE: bool
        """If the program should run in a simulated mode allowing for easy debugging."""

    def _buildConfigFromEnv(self) -> Config:
        """
        Builds a configuration object from environment variables.
        Attributes:
            VMO_VFO_SAMPLE_RATE (int): The VFO frequency in KHz.
            VMO_CENTER_FREQ (int): The center frequency in MHz.
            VMO_GAIN (str | int): The gain in dB or "auto"/None for auto gain.
            VMO_OUTPUT_SAMPLE_RATE (int): The output sample rate in Hz.
            VMO_UPLOAD_ENDPOINT_URL (str): The URL to upload the demodulated audio to.
            VMO_STATION_SOURCE_ID (int): The station source ID.
            VMO_SQUELCH (float): The value to alter to avoid squelch tripping on static.
            VMO_WAIT_TO_END (int): The time to wait for 5 seconds of quiet before ending recording.
        """

        _VFO_FS = os.getenv("VMO_VFO_SAMPLE_RATE", 250e3)
        _VFO_CTR_FREQ: str | float | None = os.getenv("VMO_CENTER_FREQ")
        _VFO_GAIN = os.getenv("VMO_GAIN", "auto")
        _OUT_FILE_FS = os.getenv("VMO_OUTPUT_SAMPLE_RATE", 6e3)
        _UPLOAD_ENDPOINT = os.getenv("VMO_UPLOAD_ENDPOINT_URL")
        _STATION_SRC_ID = os.getenv("VMO_STATION_SOURCE_ID")
        _SQUELCH = os.getenv("VMO_SQUELCH", 0.5)
        _WAIT_TO_END = os.getenv("VMO_WAIT_TO_END", 5)
        _DEBUG_MODE = os.getenv("VMO_DEBUG_MODE", False)

        if str(_DEBUG_MODE).lower() == "true":
            _DEBUG_MODE = True

        # Null checks here
        if not _VFO_FS:
            raise ValueError("VFO_FS must be set")
        if not _VFO_CTR_FREQ:
            raise ValueError("VFO_CTR_FREQ must be set")
        if not _VFO_GAIN:
            raise ValueError("VFO_GAIN must be set")
        if not _OUT_FILE_FS:
            raise ValueError("OUT_FILE_FS must be set")
        if not _UPLOAD_ENDPOINT:
            raise ValueError("UPLOAD_ENDPOINT must be set")
        if not _STATION_SRC_ID:
            raise ValueError("STATION_SRC_ID must be set")
        if not _SQUELCH:
            raise ValueError("SQUELCH must be set")
        if not _WAIT_TO_END:
            raise ValueError("WAIT_TO_END must be set")

        _VFO_CTR_FREQ = float(_VFO_CTR_FREQ) * 1e6

        builtConfig = StationController.Config(
            VFO_FS=int(_VFO_FS),
            VFO_CTR_FREQ=int(_VFO_CTR_FREQ),
            VFO_GAIN=_VFO_GAIN,
            OUT_FILE_FS=int(_OUT_FILE_FS),
            UPLOAD_ENDPOINT=str(_UPLOAD_ENDPOINT),
            STATION_SRC_ID=int(_STATION_SRC_ID),
            SQUELCH=float(_SQUELCH),
            WAIT_TO_END=int(_WAIT_TO_END),
            DEBUG_MODE=bool(_DEBUG_MODE),
        )

        print(
            "------------------- Print Full Configuration -------------------\n"
            + builtConfig.toString()
            + "\n------------------- End of Print Full Configuration. -------------------"
        )

        return builtConfig

    def _sdr_setup(self) -> RtlSdrAio:
        """
        Sets up the RTLSDR object for the station.
        """
        if self.rtlsdr:
            return self.rtlsdr

        # Check for type errors from external vars and imports
        if not RtlSdr:
            raise Exception("RtlSdr Failed to import!")

        print("Initalizing RTL")
        # Initialize radio and signal processor
        rtl = RtlSdr()
        rtl.center_freq = self.cfg.VFO_CTR_FREQ
        rtl.sample_rate = self.cfg.VFO_FS
        rtl.gain = self.cfg.VFO_GAIN

        # Return the radio object
        return rtl

    def _sdr_destroy(self):
        """
        Destroys the RTLSDR object for the station.
        """
        if not self.rtlsdr:
            return

        self.rtlsdr.stop()
        self.rtlsdr.close()
        pass

    def __init__(self, config: Config | None = None):
        """
        Initializes a new instance of the StationController class.

        Args:
            config (Config | None, optional): The configuration object. Defaults to getting the config from the environment.
        """
        if config:
            self.cfg = config
        else:
            self.cfg = self._buildConfigFromEnv()

        self.rtlsdr = None

        if self.cfg.DEBUG_MODE:
            print("DEBUG MODE: Running in simulated mode.")
            return

        self.rtlsdr = self._sdr_setup()
        pass

    def close(self):
        """
        Closes the RTL-SDR device.
        """
        self._sdr_destroy()

    async def run_stream(self) -> numpy.ndarray | numpy.complex64:
        """
        Runs the stream and collects IQ samples.
        If DEBUG_MODE is enabled, reads samples from a file. Otherwise, collects samples from the RTL-SDR device.
        Squelch is applied to filter out low power signals.
        The collected samples are stored in an array and returned.
        Returns:
            numpy.ndarray: Array of IQ samples.
        """
        if self.cfg.DEBUG_MODE or not self.rtlsdr:
            print("DEBUG MODE: Reading samples from file.")
            return numpy.fromfile("output/debugging-samples.npy", dtype=numpy.complex64)

        _wte = 0  # Wait to end counter
        _lrsi = 0  # Last recorded sample index for tracking last time squelch was actually tripped

        _samples_read = 0  # Define the start index of the samples
        _isSquelchTripped = False  # Define the squelch state as not tripped
        _iq_samples = numpy.zeros(
            10 * self.cfg.VFO_FS, dtype=numpy.complex64
        )  # Pre-allocate array at 10 seconds of samples

        # Start collecting samples to work with
        async for _readSamples in self.rtlsdr.stream():
            _isSquelchTripped = False  # Reset squelch state

            if (
                numpy.abs(_readSamples).mean() > self.cfg.SQUELCH
            ):  # This is a simple squelch
                _wte = self.cfg.WAIT_TO_END  # Reset the wait timer
                _isSquelchTripped = True
                _lrsi = _samples_read  # Record the last sample index with an actual squelch trip
                print(
                    f"Power level with squelch tripped: {numpy.abs(_readSamples).mean()}"
                )
            elif _wte > 0:
                # Set squelch tripped to true if we are waiting for transmission to end
                _wte -= 1
                _isSquelchTripped = True  # Force squelch to be tripped

            # Skip samples until squelch is tripped
            if _isSquelchTripped:
                # Negate samples below squelch threshold
                _readSamples = numpy.where(
                    numpy.abs(_readSamples) > self.cfg.SQUELCH, _readSamples, 0
                )

                # Record our samples if squelch is tripped --------------------------------
                end_idx = _samples_read + len(_readSamples)
                # make sure not to over read the number of samples
                if end_idx > len(_iq_samples):
                    _iq_samples = numpy.append(
                        _iq_samples,
                        numpy.zeros(len(_readSamples), dtype=numpy.complex64),
                    )  # This will allocate more memory for the array if needed

                print(f"Reading samples from {_samples_read} to {end_idx}")

                # Read the samples into the pre-allocated array
                _iq_samples[_samples_read:end_idx] = _readSamples[
                    0 : end_idx - _samples_read
                ]

                _samples_read = end_idx
                # Recording done ----------------------------------------------------------

            # If the wait time is over, and there is no squelch trip, stop recording
            if _wte < 1 and not _isSquelchTripped and _samples_read > 0:
                break

        # to stop streaming:
        await self.rtlsdr.stop()

        # # Run the mean levels plot
        # sp.basicPlot(_meanLevels, "Power_Levels")

        # Make sure the samples passed to the demod are only the ones with actual data
        # As well as cutting off the last wait time for the squelch + half a second of samples
        _output_samples = _iq_samples[: _lrsi + int(self.cfg.VFO_FS / 2)]

        # Save the raw samples to a file for debugging and analysis
        # current_time = datetime.datetime.now()
        # output_name = f"output/{current_time.hour:02}_{current_time.minute:02}_{current_time.second:02}_raw_samples.npy"
        # numpy.save(output_name, output_samples)

        return _output_samples
