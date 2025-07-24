const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const multer = require('multer');

// Ensure crypto is available globally for Baileys
global.crypto = crypto;

const app = express();
const PORT = 3050;

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const uploadDir = './uploads';
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    limits: {
        fileSize: 16 * 1024 * 1024 // 16MB limit
    },
    fileFilter: function (req, file, cb) {
        // Allow images, videos, audio, and documents
        const allowedMimes = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv',
            'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a',
            'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        
        if (allowedMimes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Invalid file type. Only images, videos, audio, and documents are allowed.'));
        }
    }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static('uploads')); // Serve uploaded files

// Logger
const logger = pino({ level: 'info' });

// WhatsApp socket instance
let sock = null;
let isConnected = false;
let qrCodeGenerated = false;

// Initialize WhatsApp connection
async function connectToWhatsApp() {
    try {
        const { state, saveCreds } = await useMultiFileAuthState('./auth_info');
        
        sock = makeWASocket({
            auth: state,
            logger: pino({ level: 'silent' }), // Reduce Baileys logs
            printQRInTerminal: false,
            browser: ['WhatsApp Baileys', 'Chrome', '1.0.0']
        });

        // Handle connection updates
        sock.ev.on('connection.update', (update) => {
            const { connection, lastDisconnect, qr } = update;
            
            if (qr) {
                console.log('\n=== QR CODE FOR WHATSAPP ===');
                qrcode.generate(qr, { small: true });
                console.log('Scan the QR code above with your WhatsApp mobile app');
                console.log('============================\n');
                qrCodeGenerated = true;
            }

            if (connection === 'close') {
                const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
                console.log('Connection closed due to ', lastDisconnect?.error, ', reconnecting ', shouldReconnect);
                isConnected = false;
                
                if (shouldReconnect) {
                    setTimeout(() => {
                        connectToWhatsApp();
                    }, 5000);
                } else {
                    console.log('Logged out, please restart the server and scan QR again');
                }
            } else if (connection === 'open') {
                console.log('✅ WhatsApp connection opened successfully!');
                isConnected = true;
                qrCodeGenerated = false;
            }
        });

        // Save credentials when updated
        sock.ev.on('creds.update', saveCreds);

        // Handle messages (optional - for future webhook functionality)
        sock.ev.on('messages.upsert', async (m) => {
            const message = m.messages[0];
            if (!message.key.fromMe && m.type === 'notify') {
                logger.info(`Received message from ${message.key.remoteJid}: ${message.message?.conversation || 'Media message'}`);
            }
        });

    } catch (error) {
        logger.error('Error connecting to WhatsApp:', error);
        setTimeout(() => {
            connectToWhatsApp();
        }, 5000);
    }
}

// Format phone number to WhatsApp format
function formatPhoneNumber(phone) {
    // Remove all non-digit characters
    const cleaned = phone.replace(/\D/g, '');
    
    // Add @s.whatsapp.net suffix if not present
    if (!cleaned.includes('@')) {
        return `${cleaned}@s.whatsapp.net`;
    }
    return cleaned;
}

// API Routes
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        connected: isConnected,
        qrRequired: !isConnected && !qrCodeGenerated,
        timestamp: new Date().toISOString()
    });
});

app.get('/status', (req, res) => {
    res.json({
        whatsapp_connected: isConnected,
        qr_code_required: !isConnected && !qrCodeGenerated,
        server_status: 'running',
        timestamp: new Date().toISOString()
    });
});

app.post('/send-message', async (req, res) => {
    try {
        const { phone, message } = req.body;

        if (!phone || !message) {
            return res.status(400).json({
                success: false,
                error: 'Phone number and message are required'
            });
        }

        if (!isConnected || !sock) {
            return res.status(503).json({
                success: false,
                error: 'WhatsApp not connected. Please check connection status.'
            });
        }

        const formattedPhone = formatPhoneNumber(phone);
        
        // Check if the number exists on WhatsApp
        const [result] = await sock.onWhatsApp(formattedPhone);
        if (!result?.exists) {
            return res.status(400).json({
                success: false,
                error: 'Phone number is not registered on WhatsApp'
            });
        }

        // Send the message
        const sentMessage = await sock.sendMessage(formattedPhone, { text: message });
        
        logger.info(`Message sent to ${formattedPhone}: ${message}`);
        
        res.json({
            success: true,
            message: 'Message sent successfully',
            messageId: sentMessage.key.id,
            to: formattedPhone,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Error sending message:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to send message',
            details: error.message
        });
    }
});

// Send image/media endpoint
app.post('/send-image', upload.single('image'), async (req, res) => {
    try {
        const { phone, caption } = req.body;
        const file = req.file;

        if (!phone) {
            return res.status(400).json({
                success: false,
                error: 'Phone number is required'
            });
        }

        if (!file) {
            return res.status(400).json({
                success: false,
                error: 'Image file is required'
            });
        }

        if (!isConnected || !sock) {
            return res.status(503).json({
                success: false,
                error: 'WhatsApp not connected. Please check connection status.'
            });
        }

        const formattedPhone = formatPhoneNumber(phone);
        
        // Check if the number exists on WhatsApp
        const [result] = await sock.onWhatsApp(formattedPhone);
        if (!result?.exists) {
            return res.status(400).json({
                success: false,
                error: 'Phone number is not registered on WhatsApp'
            });
        }

        // Read the uploaded file
        const fileBuffer = fs.readFileSync(file.path);
        
        // Determine message type based on file mimetype
        let messageContent = {};
        
        if (file.mimetype.startsWith('image/')) {
            messageContent = {
                image: fileBuffer,
                caption: caption || ''
            };
        } else if (file.mimetype.startsWith('video/')) {
            messageContent = {
                video: fileBuffer,
                caption: caption || ''
            };
        } else if (file.mimetype.startsWith('audio/')) {
            messageContent = {
                audio: fileBuffer,
                mimetype: file.mimetype
            };
        } else {
            // Document
            messageContent = {
                document: fileBuffer,
                mimetype: file.mimetype,
                fileName: file.originalname
            };
        }

        // Send the media message
        const sentMessage = await sock.sendMessage(formattedPhone, messageContent);
        
        // Clean up uploaded file
        fs.unlinkSync(file.path);
        
        logger.info(`Media sent to ${formattedPhone}: ${file.originalname}`);
        
        res.json({
            success: true,
            message: 'Media sent successfully',
            messageId: sentMessage.key.id,
            to: formattedPhone,
            fileName: file.originalname,
            fileType: file.mimetype,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Error sending media:', error);
        
        // Clean up uploaded file on error
        if (req.file && fs.existsSync(req.file.path)) {
            fs.unlinkSync(req.file.path);
        }
        
        res.status(500).json({
            success: false,
            error: 'Failed to send media',
            details: error.message
        });
    }
});

// Send image from URL endpoint
app.post('/send-image-url', async (req, res) => {
    try {
        const { phone, imageUrl, caption } = req.body;

        if (!phone || !imageUrl) {
            return res.status(400).json({
                success: false,
                error: 'Phone number and image URL are required'
            });
        }

        if (!isConnected || !sock) {
            return res.status(503).json({
                success: false,
                error: 'WhatsApp not connected. Please check connection status.'
            });
        }

        const formattedPhone = formatPhoneNumber(phone);
        
        // Check if the number exists on WhatsApp
        const [result] = await sock.onWhatsApp(formattedPhone);
        if (!result?.exists) {
            return res.status(400).json({
                success: false,
                error: 'Phone number is not registered on WhatsApp'
            });
        }

        // Send image from URL
        const messageContent = {
            image: { url: imageUrl },
            caption: caption || ''
        };

        const sentMessage = await sock.sendMessage(formattedPhone, messageContent);
        
        logger.info(`Image from URL sent to ${formattedPhone}: ${imageUrl}`);
        
        res.json({
            success: true,
            message: 'Image sent successfully',
            messageId: sentMessage.key.id,
            to: formattedPhone,
            imageUrl: imageUrl,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        logger.error('Error sending image from URL:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to send image from URL',
            details: error.message
        });
    }
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Baileys WhatsApp server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
    console.log(`Status check: http://localhost:${PORT}/status`);
    
    // Initialize WhatsApp connection
    connectToWhatsApp();
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down server...');
    if (sock) {
        sock.end();
    }
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
    if (sock) {
        sock.end();
    }
    process.exit(0);
});
