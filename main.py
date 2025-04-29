from station_controller import StationController
from signal_processor import SignalProcessor
from vmo_api import API
import numpy as np
import asyncio
import multiprocessing
import datetime
import tempfile


stnCtrl = StationController()
sigProc = SignalProcessor()
api = API()


def demod_output_and_upload(iq_samples: np.complex64):
    demodulated_resamped = sigProc.decimate_samples(
        stnCtrl.cfg.VFO_FS,
        stnCtrl.cfg.OUT_FILE_FS,
        sigProc.fm_demodulate(iq_samples, stnCtrl.cfg.SQUELCH, stnCtrl.cfg.VFO_FS),
    )

    sigProc.run_plots(
        demodulated_resamped, stnCtrl.cfg.VFO_FS
    )  # Just for debugging purposes

    # Convert the float32 samples to int16 to save on disk space
    demodulated_resamped = sigProc.float32_to_int16(demodulated_resamped)

    # Save the demodulated audio to a temporary file
    current_time = datetime.datetime.now()
    
    with tempfile.NamedTemporaryFile(suffix='.mp3') as temp_file:
        # Save to the temporary file
        sigProc.save_numpy_as_mp3(
            stnCtrl.cfg.OUT_FILE_FS, demodulated_resamped, temp_file.name
        )
        
        # Run the upload while the file still exists
        asyncio.run(api.upload_clip(temp_file.name, current_time, stnCtrl.cfg))
    # File is automatically deleted when the with block exits


async def main():
    while True:
        try:
            iq_samples = await stnCtrl.run_stream()
            p = multiprocessing.Process(
                target=demod_output_and_upload, args=[iq_samples]
            )
            p.start()
        except RuntimeError:
            break
        if stnCtrl.cfg.DEBUG_MODE:
            print("DEBUG MODE: Exiting after one run.")
            break

    stnCtrl.close()


if __name__ == "__main__":
    asyncio.run(main())
