from station_controller import StationController
from signal_processor import SignalProcessor
from vmo_api import API
import numpy as np
import asyncio
import multiprocessing
import datetime


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

    # Save the demodulated audio to a file
    current_time = datetime.datetime.now()
    output_name = f"output/{current_time.hour:02}_{current_time.minute:02}_{current_time.second:02}.mp3"

    sigProc.save_numpy_as_mp3(
        stnCtrl.cfg.OUT_FILE_FS, demodulated_resamped, output_name
    )

    # Run the upload
    asyncio.run(api.upload_clip(output_name, current_time, stnCtrl.cfg))


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
