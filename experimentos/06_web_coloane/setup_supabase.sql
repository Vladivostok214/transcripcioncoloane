-- =========================================================================
-- CONFIGURACIÓN DE SUPABASE: BANCO DE GLIFOS COLOANE (EXPERIMENTO 06)
-- Copia y pega este contenido completo en el SQL Editor de tu proyecto en Supabase.
-- =========================================================================

-- 1. Crear tabla para almacenar temporalmente los glifos pendientes de revisión
CREATE TABLE IF NOT EXISTS staging_glyphs (
    id TEXT PRIMARY KEY,
    line_id TEXT NOT NULL,
    page TEXT DEFAULT 'captura_externa',
    character TEXT NOT NULL,
    category TEXT NOT NULL,
    position TEXT DEFAULT 'media',
    notes TEXT DEFAULT '',
    author TEXT DEFAULT 'Colaborador',
    bbox JSONB NOT NULL,
    polygon JSONB DEFAULT '[]'::jsonb,
    crop_file TEXT NOT NULL,
    crop_isolated_file TEXT NOT NULL,
    crop_url TEXT,
    crop_iso_url TEXT,
    status TEXT DEFAULT 'pendiente',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agregar columna position si la tabla ya existía previamente
ALTER TABLE staging_glyphs ADD COLUMN IF NOT EXISTS position TEXT DEFAULT 'media';

-- 2. Habilitar políticas de seguridad (Row Level Security) para acceso público controlado
ALTER TABLE staging_glyphs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Permitir insercion publica de glifos" ON staging_glyphs;
CREATE POLICY "Permitir insercion publica de glifos" ON staging_glyphs
    FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Permitir lectura publica de glifos" ON staging_glyphs;
CREATE POLICY "Permitir lectura publica de glifos" ON staging_glyphs
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Permitir administracion de glifos" ON staging_glyphs;
CREATE POLICY "Permitir administracion de glifos" ON staging_glyphs
    FOR ALL USING (true);

-- 3. Crear Bucket de Almacenamiento para las imágenes de recortes temporales
INSERT INTO storage.buckets (id, name, public)
VALUES ('staging_crops', 'staging_crops', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- 4. Políticas de acceso para el bucket de imágenes
DROP POLICY IF EXISTS "Permitir subida de imagenes en staging_crops" ON storage.objects;
CREATE POLICY "Permitir subida de imagenes en staging_crops" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'staging_crops');

DROP POLICY IF EXISTS "Permitir lectura de imagenes en staging_crops" ON storage.objects;
CREATE POLICY "Permitir lectura de imagenes en staging_crops" ON storage.objects
    FOR SELECT USING (bucket_id = 'staging_crops');

DROP POLICY IF EXISTS "Permitir borrado de imagenes en staging_crops" ON storage.objects;
CREATE POLICY "Permitir borrado de imagenes en staging_crops" ON storage.objects
    FOR DELETE USING (bucket_id = 'staging_crops');
