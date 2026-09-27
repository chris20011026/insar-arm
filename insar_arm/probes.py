"""Small, deterministic numerical checks. No private SAR data or credentials."""
from pathlib import Path
import datetime
import itertools
import json
import os
import subprocess
import sys


def kernels():
    import numpy as np
    import isce
    from contrib.alos2proc.alos2proc import look
    from isceobj.Alos2Proc.runIonFilt import adaptive_gaussian
    rng = np.random.default_rng(847)
    a = (rng.random((64, 96)) + 1j*rng.random((64, 96))).astype(np.complex64)
    a.tofile('input.slc')
    look('input.slc', 'looks.slc', 96, 3, 4, ft=4, avg=1)
    actual = np.fromfile('looks.slc', np.complex64).reshape(16,32)
    expected = a.astype(np.complex128).reshape(16,4,32,3).mean(axis=(1,3))
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-7)
    phase = np.full((24,28), .3)
    filtered, std, window = adaptive_gaussian(phase, np.full_like(phase, .04), 11, 21, .008, fit=True)
    assert np.isfinite(filtered).all() and np.isfinite(std).all()
    np.testing.assert_allclose(filtered, phase, rtol=1e-6, atol=1e-6)
    y,x = np.mgrid[:64,:64]
    phase = (.17*x + .12*y).astype(np.float32)
    np.exp(1j*phase).astype(np.complex64).tofile('wrapped.int')
    subprocess.run(['snaphu','-s','wrapped.int','64','-o','unwrapped.bin','-C','OUTFILEFORMAT FLOAT_DATA'], check=True, timeout=60)
    unwrapped = np.fromfile('unwrapped.bin',np.float32).reshape(64,64)
    delta = unwrapped-phase
    delta -= np.median(delta)
    assert np.max(np.abs(delta)) < 1e-4
    print(json.dumps(dict(multilook_max_error=float(np.max(np.abs(actual-expected))),
                         snaphu_max_phase_error=float(np.max(np.abs(delta))))))


def plotting():
    import struct
    Path('phase').write_bytes(struct.pack('256f', *[i/256 for i in range(256)]))
    commands = [
        ['mdx','phase','-s','16','-r4','-cmap','cmy','-wrap','6.283185307179586','-P','-workdir','.'],
        ['montage','-font','DejaVu-Sans','-label','test','out.ppm','-geometry','+1','check.tif'],
        ['convert','check.tif','check.png'],
    ]
    for command in commands:
        subprocess.run(command,check=True,timeout=60)
    assert Path('check.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    print('mdx / font / PNG rendering passed')


def mintpy():
    import h5py
    import numpy as np
    dates = ['20200101','20200201','20200301','20200401']
    days = np.array([(datetime.datetime.strptime(d,'%Y%m%d')-datetime.datetime(2020,1,1)).days for d in dates])
    y,x = np.mgrid[:8,:10]
    velocity = .01*(x+y)  # known spatially varying velocity, m/year
    expected = days[:,None,None]/365.25*velocity[None,:,:]
    pairs = list(itertools.combinations(range(4),2))
    phase = np.array([-4*np.pi/.236*(expected[j]-expected[i]) for i,j in pairs],np.float32)
    with h5py.File('ifgramStack.h5','w') as f:
        f.create_dataset('date', data=np.array([[dates[i],dates[j]] for i,j in pairs],dtype='S8'))
        f.create_dataset('unwrapPhase',data=phase)
        f.create_dataset('coherence',data=np.ones_like(phase))
        f.create_dataset('connectComponent',data=np.ones_like(phase,dtype=np.int16))
        f.create_dataset('dropIfgram',data=np.ones(len(pairs),dtype=bool))
        f.create_dataset('bperp',data=np.zeros(len(pairs),dtype=np.float32))
        f.attrs.update(FILE_TYPE='ifgramStack',LENGTH='8',WIDTH='10',REF_Y='0',REF_X='0',
                       WAVELENGTH='0.236',ALOOKS='1',RLOOKS='1',UNIT='radian',PROCESSOR='isce')
    subprocess.run([sys.executable,'-m','mintpy.cli.ifgram_inversion','ifgramStack.h5','-w','no'],check=True,timeout=120)
    with h5py.File('timeseries.h5') as f:
        observed = f['timeseries'][:]
    np.testing.assert_allclose(observed,expected,atol=1e-6,rtol=1e-5)
    subprocess.run([sys.executable,'-m','mintpy.cli.timeseries2velocity','timeseries.h5'],check=True,timeout=120)
    with h5py.File('velocity.h5') as f:
        observed_velocity = f['velocity'][:]
    np.testing.assert_allclose(observed_velocity,velocity,atol=1e-5,rtol=2e-3)
    print(json.dumps(dict(timeseries_max_error_m=float(np.max(np.abs(observed-expected))),
                         velocity_max_error_m_per_year=float(np.max(np.abs(observed_velocity-velocity))))))


def generator():
    import xml.etree.ElementTree as ET
    data = Path('data').resolve()
    data.mkdir()
    for date in ['150206','151113','160219']:
        directory=data/date
        directory.mkdir()
        for name in [f'LED-ALOS2000012800-{date}-FBDR1.1__A', f'IMG-HH-ALOS2000012800-{date}-FBDR1.1__A']:
            (directory/name).write_bytes(b'SYNTHETIC COMMAND GENERATION FIXTURE - NOT SAR DATA')
    dem = Path('dem.wgs84').resolve()
    dem.write_bytes(b'\0'*16)
    image=ET.Element('imageFile')
    for key,value in [('file_name',str(dem)),('width','2'),('length','2')]:
        ET.SubElement(ET.SubElement(image,'property',name=key),'value').text=value
    ET.ElementTree(image).write(str(dem)+'.xml')
    for estimate,apply in itertools.product([False,True],repeat=2):
        root=ET.Element('stack')
        component=ET.SubElement(root,'component',name='stackinsar')
        values={'data directory':str(data),'dem for coregistration':str(dem),
                'dem for geocoding':str(dem),'water body':str(dem),
                'reference date of the stack':'151113','polarization':'HH',
                'number of subsequent dates':'2','do ionospheric phase estimation':str(estimate),
                'apply ionospheric phase correction':str(apply),
                'number of range looks 1':'3','number of azimuth looks 1':'2',
                'number of range looks 2':'4','number of azimuth looks 2':'5',
                'number of range looks ion':'16','number of azimuth looks ion':'20'}
        for key,value in values.items():
            ET.SubElement(component,'property',name=key).text=value
        ET.ElementTree(root).write('alosStack.xml')
        subprocess.run([sys.executable,str(Path(os.environ['ISCE_STACK'])/'alosStack/create_cmds.py'),
                        '-stack_par','alosStack.xml'],check=True,timeout=60)
        for n in range(1,5):
            script=Path(f'cmd_{n}.sh')
            assert script.is_file()
            subprocess.run(['/bin/bash','-n',str(script)],check=True)
        cmd3=Path('cmd_3.sh').read_text()
        assert ('ion_ls.py' in cmd3)==estimate
        assert ('ion_correct.py' in cmd3)==(estimate and apply)
        if estimate:
            assert '-nrlks1 3' in cmd3 and '-nalks_ion 20' in cmd3
    print('ALOS Stack command generation: four ion settings passed')


if __name__ == '__main__':
    {'kernels':kernels,'plotting':plotting,'mintpy':mintpy,'generator':generator}[sys.argv[1]]()
