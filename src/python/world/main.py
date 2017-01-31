# 3rd party imports
import numpy as np
from scipy.io.wavfile import read as wavread
from matplotlib import pyplot as plt

# local imports
from dio import dio
from stonemask import stonemask
from havest import havest
from cheaptrick import cheaptrick
from d4c import d4c
from synthesis import synthesis

# compare to vocoder.py


class World(object):
    def get_f0(self,  x: np.ndarray, fs: int, f0_method: str='dio') -> tuple:
        if f0_method == 'dio':
            source = dio(x, fs)
            source['f0'] = stonemask(x, fs, source['temporal_positions'], source['f0'])
        elif f0_method == 'havest':
            source = havest(x, fs)
        else:
            raise Exception
        return source['temporal_positions'], source['f0'] # or a dict

    def get_spectrum(self, x: np.ndarray, fs: int, f0_method: str='dio') -> dict:
        if f0_method == 'dio':
            source = dio(x, fs)
            source['f0'] = stonemask(x, fs, source['temporal_positions'], source['f0'])
        elif f0_method == 'havest':
            source = havest(x, fs)
        else:
            raise Exception
        filter = cheaptrick(x, fs, source)
        return {'time': source['temporal_positions'],
                'fs': source['fs'],
                'ps spectrogram': filter['ps spectrogram'],
                'world magnitude spectrogram': filter['spectrogram']}



    def encode(self, x: np.ndarray, fs: int, f0_method: str='dio') -> dict:
        if f0_method == 'dio':
            source = dio(x, fs)
            source['f0'] = stonemask(x, fs, source['temporal_positions'], source['f0'])
        elif f0_method == 'havest':
            source = havest(x, fs)
        else:
            source = dio(x, fs)
            source['f0'] = stonemask(x, fs, source['temporal_positions'], source['f0'])
        filter = cheaptrick(x, fs, source)
        source = d4c(x, fs, source)

        return {'temporal_positions': source['temporal_positions'],
                'vuv': source['vuv'],
                'fs': filter['fs'],
                'f0': source['f0'],
                'aperiodicity': source['aperiodicity'],
                'ps spectrogram': filter['ps spectrogram'],
                'spectrogram': filter['spectrogram']
                }

    def scale_pitch(self, dat: dict, factor: int) -> dict:
        dat['f0'] *= factor
        return dat

    def set_pitch(self, dat: dict, time: np.ndarray, value: np.ndarray) -> dict:
        dat['f0'] = value
        dat['temporal_positions'] = time
        return dat

    def scale_duration(self, dat: dict, factor: float) -> dict:
        dat['temporal_positions'] *= factor
        return dat

    def warp_spectrum(self, dat: dict, factor: float) -> dict:
        dat['spectrogram'][:] = np.array([np.interp(np.arange(0, len(s)) ** factor, np.arange(0, len(s)),
                            s) for s in dat['spectrogram'].T]).T
        return dat


    def decode(self, dat: dict) -> dict:
        y = synthesis(dat, dat)
        dat['out'] = y
        return dat

    def draw(self, x: np.ndarray, dat: dict):
        fs = dat['fs']
        time = dat['temporal_positions']
        y = dat['out']

        fig, ax = plt.subplots(nrows=5, figsize=(8, 6), sharex=True)
        ax[0].set_title('input signal and resynthesized-signal')
        ax[0].plot(np.arange(len(x)) / fs, x)
        ax[0].plot(np.arange(len(y)) / fs, y)
        ax[0].set_xlabel('samples')
        ax[0].legend(['original', 'synthesis'])

        X = dat['ps spectrogram']
        ax[1].set_title('pitch-synchronous spectrogram')
        ax[1].imshow(20 * np.log10(np.abs(X[:X.shape[0] // 2, :])), cmap=plt.cm.gray_r, origin='lower',
                     extent=[0, len(x) / fs, 0, fs / 2], aspect='auto')
        ax[1].set_ylabel('frequency (Hz)')
        
        ax[2].set_title('phase spectrogram')
        ax[2].imshow(np.diff(np.unwrap(np.angle(X[:X.shape[0] // 2, :]), axis=1), axis=1), cmap=plt.cm.gray_r, origin='lower',
                     extent=[0, len(x) / fs, 0, fs / 2], aspect='auto')
        ax[2].set_ylabel('frequency (Hz)')
        
        ax[3].set_title('WORLD spectrogram')
        ax[3].imshow(20 * np.log10(dat['spectrogram']), cmap=plt.cm.gray_r, origin='lower',
                     extent=[0, len(x) / fs, 0, fs / 2], aspect='auto')
        ax[3].set_ylabel('frequency (Hz)')
        
        ax[4].set_title('WORLD fundamental frequency')
        ax[4].plot(time, dat['f0'])
        ax[4].set_ylabel('time (s)')

        plt.show()



