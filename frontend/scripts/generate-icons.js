import sharp from 'sharp';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

// Helper to get directory name in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const frontendDir = path.resolve(__dirname, '..');
const sourcePath = path.join(frontendDir, 'src', 'assets', 'img', 'icon.png');
const publicDir = path.join(frontendDir, 'public');

// Ensure public directory exists
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

async function generateIcons() {
  if (!fs.existsSync(sourcePath)) {
    console.error(`Error: Source icon not found at ${sourcePath}`);
    process.exit(1);
  }

  console.log(`Using source icon: ${sourcePath}`);

  try {
    // 1. Generate standard PWA icons
    console.log('Generating pwa-192x192.png...');
    await sharp(sourcePath)
      .resize(192, 192)
      .toFile(path.join(publicDir, 'pwa-192x192.png'));

    console.log('Generating pwa-512x512.png...');
    await sharp(sourcePath)
      .resize(512, 512)
      .toFile(path.join(publicDir, 'pwa-512x512.png'));

    // 2. Generate Apple touch icon
    console.log('Generating apple-touch-icon.png...');
    await sharp(sourcePath)
      .resize(180, 180)
      .toFile(path.join(publicDir, 'apple-touch-icon.png'));

    // 3. Generate maskable icon
    // Maskable icons require a safe zone (the center 60% of the icon is guaranteed to be visible).
    // We will resize the original icon to 384x384 (75% of 512) and place it on a 512x512 background.
    console.log('Generating maskable-icon-512x512.png...');
    
    // We create a solid background of size 512x512 with app theme background color (#060709)
    const background = {
      create: {
        width: 512,
        height: 512,
        channels: 4,
        background: { r: 6, g: 7, b: 9, alpha: 1 } // #060709
      }
    };

    const resizedIconBuffer = await sharp(sourcePath)
      .resize(384, 384, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .toBuffer();

    await sharp(background)
      .composite([{ input: resizedIconBuffer, gravity: 'center' }])
      .png()
      .toFile(path.join(publicDir, 'maskable-icon-512x512.png'));

    console.log('All icons generated successfully!');
  } catch (error) {
    console.error('Error generating icons:', error);
    process.exit(1);
  }
}

generateIcons();
