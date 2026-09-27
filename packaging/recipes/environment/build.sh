#!/bin/bash
set -euo pipefail
cp "$RECIPE_DIR/LICENSE" "$SRC_DIR/LICENSE"
mkdir -p "$PREFIX/share/insar-arm" "$PREFIX/etc/conda/activate.d" "$PREFIX/etc/conda/deactivate.d" "$PREFIX/bin" "$PREFIX/etc/insar-arm-imagemagick"
cp "$RECIPE_DIR/payload/verify.py" "$RECIPE_DIR/payload/probes.py" "$PREFIX/share/insar-arm/"
cp "$RECIPE_DIR/payload/activate.sh" "$PREFIX/etc/conda/activate.d/insar-arm.sh"
cp "$RECIPE_DIR/payload/deactivate.sh" "$PREFIX/etc/conda/deactivate.d/insar-arm.sh"
printf '%s\n' '{"version":"0.2.0b1","distribution":"conda","snaphu_cs2":true}' > "$PREFIX/share/insar-arm/build-info.json"
cat > "$PREFIX/bin/insar-check" <<'SH'
#!/bin/bash
set -e
base="$(cd "$(dirname "$0")/.." && pwd)"
exec "$base/bin/python" "$base/share/insar-arm/verify.py" "$@"
SH
chmod +x "$PREFIX/bin/insar-check"
"$PYTHON" - <<'PYCODE'
import os, xml.etree.ElementTree as ET
from pathlib import Path
p = Path(os.environ['PREFIX'])
root = ET.Element('typemap')
ET.SubElement(root, 'type', name='DejaVu-Sans', fullname='DejaVu Sans', family='DejaVu Sans', style='normal', stretch='normal', weight='400', glyphs=str(p/'fonts/DejaVuSans.ttf'))
ET.ElementTree(root).write(p/'etc/insar-arm-imagemagick/type.xml', encoding='UTF-8', xml_declaration=True)
PYCODE
