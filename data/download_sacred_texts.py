#!/usr/bin/env python3
"""
Sacred Texts Archive Downloader

This script downloads the complete sacred-texts.com archive while maintaining
the original website's hierarchical organization. 

Features:
- Downloads all available texts maintaining folder structure
- Handles both zip and .txt.gz files
- Creates organized directory structure by tradition/topic
- Provides progress tracking and resume capability
- Includes metadata extraction
"""

import os
import sys
import time
import gzip
import zipfile
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen, urlretrieve, Request
from urllib.error import URLError, HTTPError
import re
from typing import List, Dict, Tuple
import json


class SacredTextsDownloader:
    def __init__(self, base_dir: str = "sacred_texts_archive"):
        self.base_url = "https://sacred-texts.com/"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.base_dir / 'download.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track downloads
        self.downloaded_files = set()
        self.failed_downloads = []
        self.download_stats = {
            'total_files': 0,
            'downloaded': 0,
            'failed': 0,
            'skipped': 0,
            'total_size_mb': 0
        }
        
        # Load existing progress if available
        self.progress_file = self.base_dir / 'download_progress.json'
        self.load_progress()

    def load_progress(self):
        """Load previous download progress"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.downloaded_files = set(data.get('downloaded_files', []))
                    self.failed_downloads = data.get('failed_downloads', [])
                    self.download_stats = data.get('stats', self.download_stats)
                self.logger.info(f"Loaded progress: {len(self.downloaded_files)} files already downloaded")
            except Exception as e:
                self.logger.warning(f"Could not load progress: {e}")

    def save_progress(self):
        """Save current download progress"""
        try:
            data = {
                'downloaded_files': list(self.downloaded_files),
                'failed_downloads': self.failed_downloads,
                'stats': self.download_stats
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save progress: {e}")

    def get_downloadable_files(self) -> List[Dict]:
        """Extract downloadable files from the download page"""
        
        # Primary large downloads from the table
        large_downloads = [
            {'path': 'bos/ibos.zip', 'size': '2.57 MB', 'type': 'zip'},
            {'path': 'bib/osrc/index.htm', 'size': '6.71 MB total', 'type': 'data'},
            {'path': 'hin/maha/mahatxt.zip', 'size': '3.37 MB', 'type': 'zip'}
        ]
        
        # Individual text files (from the numbered list)
        text_files = [
            "afr/fjort/fjo.txt.gz", "afr/mind/mind.txt.gz", "afr/wmp/wmp.txt.gz", "afr/stle/stle.txt.gz",
            "aor/darwin/origin/or.txt.gz", "aor/paine/cs/cs.txt.gz", "ame/lol/lol.txt.gz", "ame/amish/am.txt.gz",
            "ane/mba/mba.txt.gz", "ane/phc/phc.txt.gz", "ane/stc/stc.txt.gz", "ane/blc/blc.txt.gz",
            "ane/caog/caog.txt.gz", "ane/rp/rp201/rp201.txt.gz", "ane/rp/rp202/rp202.txt.gz", 
            "ane/rp/rp203/rp203.txt.gz", "ane/rp/rp204/rp204.txt.gz", "astro/ml/ml.txt.gz",
            "astro/hba/hba.txt.gz", "astro/argr/argr.txt.gz", "astro/slaa/slaa.txt.gz", "asia/jss/jss.txt.gz",
            "asia/geft/geft.txt.gz", "asia/lsbh/lsbh.txt.gz", "asia/flhl/flhl.txt.gz", "asia/tft/tft.txt.gz",
            "atl/olb/olb.txt.gz", "atl/ataw/ataw.txt.gz", "atl/tlc/tlc.txt.gz", "atl/dtp/dtp.txt.gz",
            "atl/toa/toa.txt.gz", "atl/ant/ida.txt.gz", "atl/smoa/smoa.txt.gz", "bib/fbe/fbe.txt.gz",
            "bib/lbob/lbob.txt.gz", "bib/coj/coj.txt.gz", "bib/boe/boe.txt.gz", "bib/jb/jb.txt.gz",
            "bib/csj/csj.txt.gz", "bib/biob/biob.txt.gz", "bib/cv/phai/phai.txt.gz", "bib/cv/pch/pch.txt.gz",
            "bib/cv/scb/scb.txt.gz", "bud/ami/ami.txt.gz", "bud/tbc/tbc.txt.gz", "bud/cob/cob.txt.gz",
            "bud/lob/lob.txt.gz", "bud/sbe10/sbe10.txt.gz", "bud/wov/wov.txt.gz", "bud/j1/j1.txt.gz",
            "bud/j2/j2.txt.gz", "bud/j3/j3.txt.gz", "bud/j4/j4.txt.gz", "bud/j5/j5.txt.gz",
            "bud/jt/jt.txt.gz", "bud/ettt/ettt.txt.gz", "bud/glg/glg.txt.gz", "bud/cbu/cbu.txt.gz",
            "bud/rosa/rosa.txt.gz", "bud/sahw/sahw.txt.gz", "bud/chj/chj.txt.gz", "bud/ptpl/ptpl.txt.gz",
            "bud/bups/bups.txt.gz", "bud/zfa/zfa.txt.gz", "bud/gbf/gbf.txt.gz", "neu/celt/crc/crc.txt.gz",
            "neu/celt/cuch/lgc.txt.gz", "neu/celt/gafm/gafm.txt.gz", "neu/celt/lasi/lasi.txt.gz",
            "neu/celt/tigs/tigs.txt.gz", "neu/celt/cov/cov.txt.gz", "neu/celt/mab/mab.txt.gz",
            "neu/celt/fotc/fotc.txt.gz", "neu/celt/sfft/sfft.txt.gz", "neu/celt/ftb/ftb.txt.gz",
            "neu/celt/swc1/swc1.txt.gz", "neu/celt/swc2/swc2.txt.gz", "neu/celt/ffcc/ffcc.txt.gz",
            "neu/celt/cft/cft.txt.gz", "neu/celt/cg1/cg1.txt.gz", "neu/celt/cg2/cg2.txt.gz",
            "chr/ps/ps.txt.gz", "chr/augconf/ac.txt.gz", "chr/aah/aah.txt.gz", "chr/wosf/wosf.txt.gz",
            "chr/lff/lff.txt.gz", "chr/asm/asm.txt.gz", "chr/cou/cou.txt.gz", "chr/ioc/ioc.txt.gz",
            "chr/seil/seil.txt.gz", "chr/martyrs/foxe.txt.gz", "chr/charnock/cha.txt.gz", "chr/bunyan/pp.txt.gz",
            "chr/tic/tic.txt.gz", "chr/pjc/pjc.txt.gz", "chr/mos/mos.txt.gz", "chr/hec/hec.txt.gz",
            "chr/uljc/uljc.txt.gz", "chr/balt/balt.txt.gz", "chr/lots/lots.txt.gz", "chr/did/did.txt.gz",
            "chr/jae/jae.txt.gz", "chr/agjc/agjc.txt.gz", "chr/ptp/ptp.txt.gz", "chr/toc/toc.txt.gz",
            "chr/aquinas/summa/sum.txt.gz", "cla/hh/hh.txt.gz", "cla/dep/dep.txt.gz", "cla/ebm/ebm.txt.gz",
            "cla/moc/moc.txt.gz", "cla/pr/pr.txt.gz", "cla/fsgr/fsgr.txt.gz", "cla/gpr/gpr.txt.gz",
            "cla/homer/ili/ili.txt.gz", "cla/homer/ody/ody.txt.gz", "cla/eurip/eaha/eaha.txt.gz",
            "cla/plu/pte/pte.txt.gz", "cla/plu/rgq/rgq.txt.gz", "cla/luc/tsg/tsg.txt.gz",
            "comp/otmf/otmf.txt.gz", "cfu/bop/bop.txt.gz", "cfu/boo/boo.txt.gz", "cfu/bfd/bfd.txt.gz",
            "cfu/fol/fol.txt.gz", "cfu/spc/spc.txt.gz", "cfu/mlc/mlc.txt.gz", "cfu/choc/choc.txt.gz",
            "earth/sym/sym.txt.gz", "earth/jce/jce.txt.gz", "earth/smog/smog.txt.gz", "earth/atec/atec.txt.gz",
            "earth/pell/pell.txt.gz", "earth/ams/ams.txt.gz", "earth/osgp/osgp.txt.gz", "earth/hhp/hhp.txt.gz",
            "egy/rtae/rtae.txt.gz", "egy/eml/eml.txt.gz", "egy/ael/ael.txt.gz", "neu/eng/mect/mect.txt.gz",
            "neu/eng/tfc/tfc.txt.gz", "neu/eng/sie/sie.txt.gz", "neu/eng/str/str.txt.gz",
            "eso/pym/pym.txt.gz", "eso/vow/vow.txt.gz", "eso/ldjb/ldjb.txt.gz", "eso/aww/aww.txt.gz",
            "eso/wsl/wsl.txt.gz", "eso/cc/cc.txt.gz", "eso/sob/sob.txt.gz", "eso/cuts/cuts.txt.gz",
            "eso/nop/nop.txt.gz", "eso/kyb/kyb.txt.gz", "eso/cjb/cjb.txt.gz", "eso/pnm/pnm.txt.gz",
            "eso/osi/osi.txt.gz", "eso/ihas/ihas.txt.gz", "eso/to/to.txt.gz", "eso/khw/khw.txt.gz",
            "evil/hod/hod.txt.gz", "evil/tee/tee.txt.gz", "evil/dwf/dwf.txt.gz", "evil/dol/dol.txt.gz",
            "fort/damn/damn.txt.gz", "fort/land/land.txt.gz", "fort/lo/lo.txt.gz", "fort/wild/wild.txt.gz",
            "mas/morgan/morg.txt.gz", "mas/dun/dun.txt.gz", "mas/gar/gar.txt.gz", "mas/md/md.txt.gz",
            "mas/shib/shib.txt.gz", "mas/bui/bui.txt.gz", "mas/mom/mom.txt.gz", "mas/syma/syma.txt.gz",
            "goth/vkk/vkk.txt.gz", "goth/bow/bow.txt.gz", "goth/frank/frank.txt.gz", "goth/drac/drac.txt.gz",
            "gno/fff/fff.txt.gz", "gno/gar/gar.txt.gz", "gno/th1/th1.txt.gz", "gno/th2/th2.txt.gz",
            "gno/th3/th3.txt.gz", "hin/sbe32/sbe32.txt.gz", "hin/sbe46/sbe46.txt.gz", "hin/av/av.txt.gz",
            "hin/sbe01/sbe01.txt.gz", "hin/sbe15/sbe15.txt.gz", "hin/tmu/tmu.txt.gz", "hin/ftu/ftu.txt.gz",
            "hin/vp/vp.txt.gz", "hin/gpu/gpu.txt.gz", "hin/kmu/kmu.txt.gz", "hin/dutt/dutt.txt.gz",
            "hin/sbg/sbg.txt.gz", "hin/brk/brk.txt.gz", "hin/wos/wos.txt.gz", "hin/ysp/ysp.txt.gz",
            "hin/dast/dast.txt.gz", "hin/htss/htss.txt.gz", "hin/sok/sok.txt.gz", "hin/yvhf/yvhf.txt.gz",
            "hin/gork/gork.txt.gz", "hin/hmvp/hmvp.txt.gz", "hin/kyog/kyog.txt.gz", "isl/qr/qr.txt.gz",
            "isl/pick/pick.txt.gz", "isl/yaq/yaq.txt.gz", "isl/omy/omy.txt.gz", "isl/spa/spa.txt.gz",
            "isl/mes/mes.txt.gz", "isl/masnavi/msn.txt.gz", "isl/saab/saab.txt.gz", "isl/bus/bus.txt.gz",
            "isl/zun/zun.txt.gz", "isl/srg/srg.txt.gz", "isl/daa/daa.txt.gz", "isl/rok/rok.txt.gz",
            "isl/arp/arp.txt.gz", "isl/arw/arw.txt.gz", "neu/poe/poe.txt.gz", "neu/nda/nda.txt.gz",
            "neu/ice/coo/coo.txt.gz", "jai/sbe22/sbe22.txt.gz", "jai/sbe45/sbe45.txt.gz", "jud/etm/etm.txt.gz",
            "jud/wott/wott.txt.gz", "jud/pol/pol.txt.gz", "jud/bata/bata.txt.gz", "jud/spb/spb.txt.gz",
            "jud/gfp/gfp.txt.gz", "jud/doth/doth.txt.gz", "jud/ajp/ajp.txt.gz", "jud/gm/gm.txt.gz",
            "neu/mbh/mbh.txt.gz", "neu/tml/tml.txt.gz", "neu/rft/rft.txt.gz", "neu/sfs/sfs.txt.gz",
            "neu/ftr/ftr.txt.gz", "neu/oprt/oprt.txt.gz", "neu/kveng/kv.txt.gz", "neu/ftmg/ftmg.txt.gz",
            "neu/ptn/ptn.txt.gz", "lcr/abs/abs.txt.gz", "lcr/fsca/fsca.txt.gz", "lcr/eod/eod.txt.gz",
            "lgbt/itp/itp.txt.gz", "etc/vre/vre.txt.gz", "etc/ml/ml.txt.gz", "etc/lou/lou.txt.gz",
            "etc/ddl/ddl.txt.gz", "etc/fwe/fwe.txt.gz", "mor/dc/dc.txt.gz", "mor/hou/hou.txt.gz",
            "myst/myst/myst.txt.gz", "nam/por/por.txt.gz", "nam/mmp/mmp.txt.gz", "nam/ca/dow/dow.txt.gz",
            "nam/ca/cma/cma.txt.gz", "nam/ca/yat/yat.txt.gz", "nam/hopi/toth/toth.txt.gz", "nam/inca/oll/oll.txt.gz",
            "nam/nav/sws/sws.txt.gz", "nam/ne/al/al.txt.gz", "nam/nw/ttb/ttb.txt.gz", "nam/pla/ont/ont.txt.gz",
            "nam/sw/dg/dg.txt.gz", "nam/sw/sot/sot.txt.gz", "nth/elms/elms.txt.gz", "nth/dlms/dlms.txt.gz",
            "nth/twi/twi.txt.gz", "nth/sgr/sgr.txt.gz", "nth/yfhu/yfhu.txt.gz", "nth/mks/mks.txt.gz",
            "nth/qm/qm.txt.gz", "nth/tsoa/tsoa.txt.gz", "nth/tgr/tgr.txt.gz", "nth/ssbm/ssbm.txt.gz",
            "nth/ssug/ssug.txt.gz", "pag/wcwe/wcwe.txt.gz", "pag/gsft/gsft.txt.gz", "pag/scott/ldw.txt.gz",
            "pag/sor/sor.txt.gz", "pag/iwd/iwd.txt.gz", "nos/oon/oon.txt.gz", "pac/ulh/ulh.txt.gz",
            "pac/hft/hft.txt.gz", "pac/maui/maui.txt.gz", "psi/mrad/mrad.txt.gz", "neu/roma/gft/gft.txt.gz",
            "neu/morris/thol/thol.txt.gz", "neu/morris/rotm/rotm.txt.gz", "neu/morris/thow/thow.txt.gz",
            "neu/morris/sglt/sglt.txt.gz", "neu/morris/chc/chc.txt.gz", "neu/morris/wwe/wwe.txt.gz",
            "neu/morris/wwi/wwi.txt.gz", "neu/morris/sunf/sunf.txt.gz", "neu/yeats/twi/twi.txt.gz",
            "neu/dun/gope/gope.txt.gz", "neu/dun/tago/tago.txt.gz", "neu/dun/swos/swos.txt.gz",
            "neu/dun/adta/adta.txt.gz", "neu/dun/swld/swld.txt.gz", "neu/dun/tbow/tbow.txt.gz",
            "neu/dun/fotd/fotd.txt.gz", "neu/dun/tawo/tawo.txt.gz", "neu/dun/pgam/pgam.txt.gz",
            "neu/dun/doro/doro.txt.gz", "neu/lfb/bl/blfb.txt.gz", "neu/lfb/br/brfb.txt.gz",
            "neu/lfb/cr/crfb.txt.gz", "neu/lfb/gn/gnfb.txt.gz", "neu/lfb/gy/gyfb.txt.gz",
            "neu/lfb/li/lifb.txt.gz", "neu/lfb/ol/olfb.txt.gz", "neu/lfb/or/orfb.txt.gz",
            "neu/lfb/pi/pifb.txt.gz", "neu/lfb/re/refb.txt.gz", "neu/lfb/vi/vifb.txt.gz",
            "neu/lfb/ye/yefb.txt.gz", "sex/kama/ks.txt.gz", "sks/flos/flos.txt.gz", "sha/sis/sis.txt.gz",
            "shi/kj/kj.txt.gz", "shi/gen/gen.txt.gz", "shi/bsd/bsd.txt.gz", "shi/hvj/hvj.txt.gz",
            "shi/atfj/atfj.txt.gz", "sym/mosy/mosy.txt.gz", "sym/bot/bot.txt.gz", "sro/pc/pc.txt.gz",
            "sro/mhj/mhj3.txt.gz", "sro/csg/csg.txt.gz", "sro/mmm/mmm.txt.gz", "sro/sma/sma.txt.gz",
            "sro/hkt/hkt.txt.gz", "sro/rhr/rhr.txt.gz", "sro/wta/wta.txt.gz", "tao/mt/mt.txt.gz",
            "tao/ltw/ltw.txt.gz", "tao/salt/salt.txt.gz", "tao/aow/aow.txt.gz", "tao/mcm/mcm.txt.gz",
            "tao/kfu/kfu.txt.gz", "tarot/pkt/pkt.txt.gz", "tarot/ftc/ftc.txt.gz", "ring/wbw/wbw.txt.gz",
            "ring/two/two.txt.gz", "ufo/fsar/fsar.txt.gz"
        ]
        
        # Combine all files
        all_files = []
        
        # Add large downloads
        for item in large_downloads:
            all_files.append({
                'path': item['path'],
                'url': urljoin(self.base_url, item['path']),
                'type': item['type'],
                'size': item['size']
            })
        
        # Add individual text files
        for path in text_files:
            all_files.append({
                'path': path,
                'url': urljoin(self.base_url, path),
                'type': 'txt.gz',
                'size': 'Unknown'
            })
        
        self.download_stats['total_files'] = len(all_files)
        return all_files

    def download_file(self, file_info: Dict) -> bool:
        """Download a single file maintaining directory structure"""
        url = file_info['url']
        rel_path = file_info['path']
        
        # Skip if already downloaded
        if rel_path in self.downloaded_files:
            self.download_stats['skipped'] += 1
            return True
        
        # Create directory structure
        local_path = self.base_dir / rel_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.logger.info(f"Downloading: {rel_path}")
            
            # Create request with proper User-Agent to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Download with progress
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) / total_size)
                    size_mb = total_size / (1024 * 1024)
                    print(f"\r  Progress: {percent:.1f}% ({size_mb:.2f} MB)", end='', flush=True)
            
            # Use urllib with custom headers
            req = Request(url, headers=headers)
            with urlopen(req) as response:
                with open(local_path, 'wb') as f:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded = 0
                    block_size = 8192
                    
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = min(100, (downloaded * 100) / total_size)
                            size_mb = total_size / (1024 * 1024)
                            print(f"\r  Progress: {percent:.1f}% ({size_mb:.2f} MB)", end='', flush=True)
            print()  # New line after progress
            
            # Track success
            self.downloaded_files.add(rel_path)
            self.download_stats['downloaded'] += 1
            
            # Get file size
            file_size_mb = local_path.stat().st_size / (1024 * 1024)
            self.download_stats['total_size_mb'] += file_size_mb
            
            self.logger.info(f"✓ Downloaded: {rel_path} ({file_size_mb:.2f} MB)")
            
            # Save progress periodically
            if self.download_stats['downloaded'] % 10 == 0:
                self.save_progress()
            
            return True
            
        except (URLError, HTTPError) as e:
            self.logger.error(f"✗ Failed to download {rel_path}: {e}")
            self.failed_downloads.append({'path': rel_path, 'error': str(e)})
            self.download_stats['failed'] += 1
            return False
        except Exception as e:
            self.logger.error(f"✗ Unexpected error downloading {rel_path}: {e}")
            self.failed_downloads.append({'path': rel_path, 'error': str(e)})
            self.download_stats['failed'] += 1
            return False

    def extract_files(self):
        """Extract compressed files maintaining structure"""
        self.logger.info("Extracting compressed files...")
        
        extracted_dir = self.base_dir / "extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        # Find all .gz and .zip files
        for file_path in self.base_dir.rglob("*.gz"):
            if file_path.name.endswith('.txt.gz'):
                try:
                    # Create corresponding directory in extracted
                    rel_path = file_path.relative_to(self.base_dir)
                    extract_path = extracted_dir / rel_path.with_suffix('')  # Remove .gz
                    extract_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract
                    with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as gz_file:
                        with open(extract_path, 'w', encoding='utf-8') as txt_file:
                            txt_file.write(gz_file.read())
                    
                    self.logger.info(f"Extracted: {rel_path}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to extract {file_path}: {e}")
        
        # Extract zip files
        for file_path in self.base_dir.rglob("*.zip"):
            try:
                rel_path = file_path.relative_to(self.base_dir)
                extract_dir = extracted_dir / rel_path.stem
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    zip_file.extractall(extract_dir)
                
                self.logger.info(f"Extracted ZIP: {rel_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to extract ZIP {file_path}: {e}")

    def create_metadata(self):
        """Create metadata about the downloaded collection"""
        metadata = {
            'download_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'sacred-texts.com',
            'stats': self.download_stats,
            'failed_downloads': self.failed_downloads,
            'total_files_downloaded': len(self.downloaded_files),
            'archive_structure': self.get_directory_structure()
        }
        
        metadata_file = self.base_dir / 'collection_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Created metadata: {metadata_file}")

    def get_directory_structure(self) -> Dict:
        """Get overview of directory structure"""
        structure = {}
        
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = file_path.relative_to(self.base_dir)
                category = str(rel_path.parts[0]) if rel_path.parts else 'root'
                
                if category not in structure:
                    structure[category] = {'files': 0, 'size_mb': 0}
                
                structure[category]['files'] += 1
                structure[category]['size_mb'] += file_path.stat().st_size / (1024 * 1024)
        
        return structure

    def download_all(self):
        """Download complete sacred texts archive"""
        self.logger.info("Starting Sacred Texts Archive download...")
        self.logger.info(f"Base directory: {self.base_dir.absolute()}")
        
        # Get all downloadable files
        files_to_download = self.get_downloadable_files()
        self.logger.info(f"Found {len(files_to_download)} files to download")
        
        # Download files
        start_time = time.time()
        for i, file_info in enumerate(files_to_download, 1):
            print(f"\n[{i}/{len(files_to_download)}] Processing: {file_info['path']}")
            self.download_file(file_info)
            
            # Small delay to be respectful
            time.sleep(1)
        
        # Save final progress
        self.save_progress()
        
        # Create metadata
        self.create_metadata()
        
        # Extract files
        extract_choice = input("\nExtract compressed files? (y/n): ").lower().strip()
        if extract_choice == 'y':
            self.extract_files()
        
        # Print summary
        elapsed = time.time() - start_time
        self.logger.info("\n" + "="*50)
        self.logger.info("DOWNLOAD COMPLETE")
        self.logger.info("="*50)
        self.logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
        self.logger.info(f"Files downloaded: {self.download_stats['downloaded']}")
        self.logger.info(f"Files failed: {self.download_stats['failed']}")
        self.logger.info(f"Files skipped: {self.download_stats['skipped']}")
        self.logger.info(f"Total size: {self.download_stats['total_size_mb']:.1f} MB")
        self.logger.info(f"Archive location: {self.base_dir.absolute()}")
        
        if self.failed_downloads:
            self.logger.info(f"\nFailed downloads saved to: {self.progress_file}")


def main():
    """Main entry point"""
    print("Sacred Texts Archive Downloader")
    print("===============================")
    print("This will download the complete sacred-texts.com archive")
    print("maintaining the original website structure.")
    print("\nEstimated total size: ~4-5 GB")
    print("Time required: ~30-60 minutes (depending on connection)")
    
    # Get base directory
    default_dir = "sacred_texts_archive"
    base_dir = input(f"\nDownload directory [{default_dir}]: ").strip() or default_dir
    
    # Confirm download
    print(f"\nDownload will begin to: {Path(base_dir).absolute()}")
    confirm = input("Continue? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("Download cancelled.")
        return
    
    # Start download
    downloader = SacredTextsDownloader(base_dir)
    try:
        downloader.download_all()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        downloader.save_progress()
        print("Progress saved. Run script again to resume.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        downloader.save_progress()
        raise


if __name__ == "__main__":
    main()
