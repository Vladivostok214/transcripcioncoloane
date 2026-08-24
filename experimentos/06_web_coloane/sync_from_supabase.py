"""
Script CLI: sync_from_supabase.py
=================================
Descarga directamente los glifos pendientes desde Supabase hacia la carpeta local
experimentos/06_web_coloane/, actualiza dataset_glifos_manuales.json y dataset_glifos_manuales.csv,
y purga los registros sincronizados de Supabase.

Uso:
    python experimentos/06_web_coloane/sync_from_supabase.py
"""

import os
import sys
import json
import csv
import urllib.request
import urllib.parse
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

SUPABASE_URL = "https://pqkvxewberkkihiaqizt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxa3Z4ZXdiZXJra2loaWFxaXp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1MjMwNDAsImV4cCI6MjEwMzA5OTA0MH0.2g35E4w4Haw0mlKvZab20yHp43wU8DZ6KVeMB7rV9pk"

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
CROPS_DIR = os.path.join(EXP_DIR, "crops")
CROPS_ISO_DIR = os.path.join(EXP_DIR, "crops_isolated")
JSON_PATH = os.path.join(EXP_DIR, "dataset_glifos_manuales.json")
CSV_PATH = os.path.join(EXP_DIR, "dataset_glifos_manuales.csv")

os.makedirs(CROPS_DIR, exist_ok=True)
os.makedirs(CROPS_ISO_DIR, exist_ok=True)

def fetch_pending_glyphs():
    url = f"{SUPABASE_URL}/rest/v1/staging_glyphs?status=eq.pendiente&order=created_at.asc"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    })
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error al consultar Supabase: {e}")
        return []

def download_image(storage_filename, dest_path):
    encoded_name = urllib.parse.quote(storage_filename)
    url = f"{SUPABASE_URL}/storage/v1/object/public/staging_crops/{encoded_name}"
    try:
        urllib.request.urlretrieve(url, dest_path)
        return True
    except Exception as e:
        print(f"⚠️ Aviso al descargar {storage_filename}: {e}")
        return False

def purge_from_supabase(synced_ids, synced_files):
    # 1. Borrar filas de staging_glyphs
    ids_param = ",".join(f'"{i}"' for i in synced_ids)
    url = f"{SUPABASE_URL}/rest/v1/staging_glyphs?id=in.({ids_param})"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }, method="DELETE")
    try:
        urllib.request.urlopen(req)
        print("  ✓ Filas eliminadas de staging_glyphs en Supabase")
    except Exception as e:
        print(f"  ⚠️ Error al borrar filas de Supabase: {e}")

    # 2. Borrar imágenes del bucket
    if synced_files:
        del_url = f"{SUPABASE_URL}/storage/v1/object/staging_crops"
        payload = json.dumps({"prefixes": synced_files}).encode('utf-8')
        req_del = urllib.request.Request(del_url, data=payload, headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }, method="DELETE")
        try:
            urllib.request.urlopen(req_del)
            print("  ✓ Imágenes eliminadas del bucket staging_crops en Supabase")
        except Exception as e:
            print(f"  ⚠️ Error al borrar imágenes de Storage: {e}")

def main():
    print("=" * 60)
    print("  SINCRONIZADOR CLI SUPABASE -> LOCAL (Exp 06)")
    print("=" * 60)

    print("📡 Consultando glifos pendientes en Supabase...")
    pending = fetch_pending_glyphs()
    if not pending:
        print("✨ No hay glifos pendientes para sincronizar en Supabase.")
        return

    print(f"📥 Se encontraron {len(pending)} glifos pendientes. Descargando...")

    # Cargar base de datos local existente
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            local_db = json.load(f)
    else:
        local_db = {"metadata": {"total_glyphs": 0, "captures_count": 0}, "glyphs": []}

    existing_ids = {g['id'] for g in local_db.get('glyphs', [])}
    synced_ids = []
    synced_files = []

    for g in pending:
        gid = g['id']
        crop_file = g.get('crop_file', f"{gid}.png")
        crop_iso_file = g.get('crop_isolated_file', f"{gid}_iso.png")

        # Descargar crops a carpetas locales
        download_image(crop_file, os.path.join(CROPS_DIR, crop_file))
        download_image(crop_iso_file, os.path.join(CROPS_ISO_DIR, crop_iso_file))

        synced_files.extend([crop_file, crop_iso_file])
        synced_ids.append(gid)

        if gid not in existing_ids:
            local_db['glyphs'].append({
                "id": gid,
                "line_id": g.get('line_id'),
                "page": g.get('page', 'captura_externa'),
                "character": g.get('character'),
                "category": g.get('category'),
                "notes": g.get('notes', ''),
                "author": g.get('author', 'Colaborador'),
                "bbox": g.get('bbox', [0, 0, 0, 0]),
                "polygon": g.get('polygon', []),
                "crop_file": crop_file,
                "crop_isolated_file": crop_iso_file
            })
            existing_ids.add(gid)

    # Actualizar metadatos
    lines_set = {g.get('line_id') for g in local_db['glyphs']}
    local_db['metadata'] = {
        "total_glyphs": len(local_db['glyphs']),
        "captures_count": len(lines_set),
        "last_updated": "Wladimir (CLI Sync)",
        "last_sync": datetime.now().isoformat()
    }

    # Guardar JSON
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(local_db, f, indent=2, ensure_ascii=False)
    print(f"  ✓ {JSON_PATH} actualizado ({len(local_db['glyphs'])} glifos totales)")

    # Guardar CSV
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Capture_ID", "Page", "Character", "Category", "Notes", "BBox_X", "BBox_Y", "BBox_W", "BBox_H", "Polygon", "Crop_File", "Crop_Isolated_File", "Author"])
        for g in local_db['glyphs']:
            b = g.get('bbox', [0, 0, 0, 0])
            poly = g.get('polygon', [])
            poly_str = json.dumps(poly) if poly else ""
            writer.writerow([
                g.get('id'),
                g.get('line_id'),
                g.get('page', 'captura_externa'),
                g.get('character'),
                g.get('category'),
                g.get('notes', ''),
                b[0], b[1], b[2], b[3],
                poly_str,
                g.get('crop_file', ''),
                g.get('crop_isolated_file', ''),
                g.get('author', 'Colaborador')
            ])
    print(f"  ✓ {CSV_PATH} actualizado")

    # Purgar Supabase
    print("🧹 Purgando buffer temporal en Supabase...")
    purge_from_supabase(synced_ids, synced_files)

    print("\n🎉 ¡Sincronización completada exitosamente!")
    print(f"   Nuevos glifos incorporados: {len(pending)}")
    print(f"   Total en catálogo maestro: {len(local_db['glyphs'])}")

if __name__ == '__main__':
    main()
