// Vercel Serverless Function: api/sync_github.js
// Sincroniza atómicamente los glifos aprobados de Supabase hacia GitHub en un único commit,
// y purga el almacenamiento temporal en Supabase.

export default async function handler(req, res) {
    // Configuración de CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ status: 'error', message: 'Método no permitido. Usa POST.' });
    }

    const GITHUB_TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
    const GITHUB_REPO = process.env.GITHUB_REPO || 'Vladivostok214/transcripcioncoloane';
    const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';

    const SUPABASE_URL = process.env.SUPABASE_URL || 'https://pqkvxewberkkihiaqizt.supabase.co';
    const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxa3Z4ZXdiZXJra2loaWFxaXp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1MjMwNDAsImV4cCI6MjEwMzA5OTA0MH0.2g35E4w4Haw0mlKvZab20yHp43wU8DZ6KVeMB7rV9pk';

    if (!GITHUB_TOKEN) {
        return res.status(400).json({
            status: 'error',
            message: 'Falta la variable de entorno GITHUB_TOKEN en la configuración de Vercel.'
        });
    }

    try {
        // 1. Obtener glifos pendientes desde Supabase
        const stagingRes = await fetch(`${SUPABASE_URL}/rest/v1/staging_glyphs?status=eq.pendiente&order=created_at.asc`, {
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`
            }
        });

        if (!stagingRes.ok) {
            throw new Error(`Error al consultar Supabase: ${stagingRes.status} ${await stagingRes.text()}`);
        }

        const stagingGlyphs = await stagingRes.json();
        if (!stagingGlyphs || stagingGlyphs.length === 0) {
            return res.status(200).json({
                status: 'ok',
                message: 'No hay glifos pendientes para sincronizar en Supabase.',
                synced_count: 0
            });
        }

        // 2. Descargar las imágenes de cada glifo desde Supabase Storage
        const fileBlobsToCommit = [];
        const filesToPurge = [];

        for (const g of stagingGlyphs) {
            // Descargar RGB crop
            if (g.crop_file) {
                const rgbUrl = `${SUPABASE_URL}/storage/v1/object/public/staging_crops/${g.crop_file}`;
                const rRes = await fetch(rgbUrl);
                if (rRes.ok) {
                    const buf = await rRes.arrayBuffer();
                    const b64 = Buffer.from(buf).toString('base64');
                    fileBlobsToCommit.push({
                        path: `experimentos/06_web_coloane/crops/${g.crop_file}`,
                        content: b64,
                        encoding: 'base64'
                    });
                    filesToPurge.push(g.crop_file);
                }
            }

            // Descargar Isolated RGBA crop
            if (g.crop_isolated_file) {
                const isoUrl = `${SUPABASE_URL}/storage/v1/object/public/staging_crops/${g.crop_isolated_file}`;
                const iRes = await fetch(isoUrl);
                if (iRes.ok) {
                    const buf = await iRes.arrayBuffer();
                    const b64 = Buffer.from(buf).toString('base64');
                    fileBlobsToCommit.push({
                        path: `experimentos/06_web_coloane/crops_isolated/${g.crop_isolated_file}`,
                        content: b64,
                        encoding: 'base64'
                    });
                    filesToPurge.push(g.crop_isolated_file);
                }
            }
        }

        // 3. Obtener el archivo JSON actual desde GitHub
        const ghJsonUrl = `https://api.github.com/repos/${GITHUB_REPO}/contents/experimentos/06_web_coloane/dataset_glifos_manuales.json?ref=${GITHUB_BRANCH}`;
        const ghJsonRes = await fetch(ghJsonUrl, {
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'Coloane-Annotator-Web'
            }
        });

        let currentDb = { metadata: { total_glyphs: 0, captures_count: 0 }, glyphs: [] };
        if (ghJsonRes.ok) {
            const ghJsonData = await ghJsonRes.json();
            const rawContent = Buffer.from(ghJsonData.content, 'base64').toString('utf-8');
            currentDb = JSON.parse(rawContent);
        }

        // 4. Fusionar glifos nuevos evitando duplicados
        const existingIds = new Set(currentDb.glyphs.map(x => x.id));
        for (const g of stagingGlyphs) {
            if (!existingIds.has(g.id)) {
                currentDb.glyphs.push({
                    id: g.id,
                    line_id: g.line_id,
                    page: g.page || 'captura_externa',
                    character: g.character,
                    category: g.category,
                    position: g.position || 'media',
                    notes: g.notes || '',
                    author: g.author || 'Colaborador',
                    bbox: Array.isArray(g.bbox) ? g.bbox : [0, 0, 0, 0],
                    polygon: Array.isArray(g.polygon) ? g.polygon : [],
                    crop_file: g.crop_file,
                    crop_isolated_file: g.crop_isolated_file
                });
                existingIds.add(g.id);
            }
        }

        const linesSet = new Set(currentDb.glyphs.map(g => g.line_id));
        currentDb.metadata = {
            total_glyphs: currentDb.glyphs.length,
            captures_count: linesSet.size,
            last_updated: req.body?.author || 'Wladimir',
            last_sync: new Date().toISOString()
        };

        const updatedJsonStr = JSON.stringify(currentDb, null, 2);

        // Generar CSV actualizado
        const csvRows = [
            ["ID", "Capture_ID", "Page", "Character", "Category", "Position", "Notes", "BBox_X", "BBox_Y", "BBox_W", "BBox_H", "Polygon", "Crop_File", "Crop_Isolated_File", "Author"]
        ];
        for (const g of currentDb.glyphs) {
            const b = g.bbox || [0, 0, 0, 0];
            const polyStr = (g.polygon && g.polygon.length > 0) ? JSON.stringify(g.polygon) : '';
            csvRows.push([
                g.id,
                g.line_id,
                g.page || 'captura_externa',
                g.character,
                g.category,
                g.position || 'media',
                `"${(g.notes || '').replace(/"/g, '""')}"`,
                b[0], b[1], b[2], b[3],
                `"${polyStr.replace(/"/g, '""')}"`,
                g.crop_file,
                g.crop_isolated_file,
                g.author || 'Colaborador'
            ]);
        }
        const updatedCsvStr = csvRows.map(r => r.join(',')).join('\n');

        // Agregar JSON y CSV a los archivos a commitear
        fileBlobsToCommit.push({
            path: 'experimentos/06_web_coloane/dataset_glifos_manuales.json',
            content: Buffer.from(updatedJsonStr, 'utf-8').toString('base64'),
            encoding: 'base64'
        });
        fileBlobsToCommit.push({
            path: 'experimentos/06_web_coloane/dataset_glifos_manuales.csv',
            content: Buffer.from(updatedCsvStr, 'utf-8').toString('base64'),
            encoding: 'base64'
        });

        // 5. Crear Blobs en GitHub Git Data API
        const treeItems = [];
        for (const f of fileBlobsToCommit) {
            const blobRes = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/git/blobs`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${GITHUB_TOKEN}`,
                    'Accept': 'application/vnd.github+json',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Coloane-Annotator-Web'
                },
                body: JSON.stringify({ content: f.content, encoding: f.encoding })
            });

            if (!blobRes.ok) {
                throw new Error(`Error creando blob para ${f.path}: ${await blobRes.text()}`);
            }

            const blobData = await blobRes.json();
            treeItems.push({
                path: f.path,
                mode: '100644',
                type: 'blob',
                sha: blobData.sha
            });
        }

        // 6. Obtener último commit SHA de la rama
        const refRes = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/git/ref/heads/${GITHUB_BRANCH}`, {
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'Coloane-Annotator-Web'
            }
        });
        const refData = await refRes.json();
        const latestCommitSha = refData.object.sha;

        // Obtener el Tree SHA del último commit
        const commitRes = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/git/commits/${latestCommitSha}`, {
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'Coloane-Annotator-Web'
            }
        });
        const commitData = await commitRes.json();
        const baseTreeSha = commitData.tree.sha;

        // 7. Crear el nuevo Git Tree
        const newTreeRes = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/git/trees`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json',
                'User-Agent': 'Coloane-Annotator-Web'
            },
            body: JSON.stringify({
                base_tree: baseTreeSha,
                tree: treeItems
            })
        });
        const newTreeData = await newTreeRes.json();
        const newTreeSha = newTreeData.sha;

        // 8. Crear el nuevo Commit
        const todayStr = new Date().toISOString().split('T')[0];
        const commitMsg = `feat(dataset): sincronizar lote de ${stagingGlyphs.length} nuevos glifos (Total: ${currentDb.glyphs.length}) - ${todayStr}`;
        const createCommitRes = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/git/commits`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json',
                'User-Agent': 'Coloane-Annotator-Web'
            },
            body: JSON.stringify({
                message: commitMsg,
                tree: newTreeSha,
                parents: [latestCommitSha]
            })
        });
        const createdCommitData = await createCommitRes.json();
        const finalCommitSha = createdCommitData.sha;

        // 9. Actualizar la referencia de la rama main
        await fetch(`https://api.github.com/repos/${GITHUB_REPO}/git/refs/heads/${GITHUB_BRANCH}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github+json',
                'Content-Type': 'application/json',
                'User-Agent': 'Coloane-Annotator-Web'
            },
            body: JSON.stringify({
                sha: finalCommitSha,
                force: false
            })
        });

        // 10. Purgar los glifos sincronizados de Supabase (Base de datos y Storage)
        const syncedIds = stagingGlyphs.map(g => g.id);
        await fetch(`${SUPABASE_URL}/rest/v1/staging_glyphs?id=in.(${syncedIds.map(id => `"${id}"`).join(',')})`, {
            method: 'DELETE',
            headers: {
                'apikey': SUPABASE_KEY,
                'Authorization': `Bearer ${SUPABASE_KEY}`
            }
        });

        if (filesToPurge.length > 0) {
            await fetch(`${SUPABASE_URL}/storage/v1/object/staging_crops`, {
                method: 'DELETE',
                headers: {
                    'apikey': SUPABASE_KEY,
                    'Authorization': `Bearer ${SUPABASE_KEY}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ prefixes: filesToPurge })
            });
        }

        return res.status(200).json({
            status: 'ok',
            synced_count: stagingGlyphs.length,
            total_glyphs: currentDb.glyphs.length,
            commit_sha: finalCommitSha,
            message: `Sincronización exitosa: ${stagingGlyphs.length} glifos guardados en GitHub y cola de Supabase limpiada.`
        });

    } catch (err) {
        console.error("Error en sync_github:", err);
        return res.status(500).json({
            status: 'error',
            message: err.message || 'Error interno al sincronizar con GitHub.'
        });
    }
}
