// Enhanced Neon Rhythm Game
// Core game engine with optimizations and visual effects

class RhythmGame {
    constructor() {
        this.canvas = document.getElementById('rhythmCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.audio = document.getElementById('gameAudio');
        
        // Game constants
        this.WIDTH = this.canvas.width;
        this.HEIGHT = this.canvas.height;
        this.NOTE_SPEED = 1.0; // 25% of normal speed for better synchronization
        this.HIT_ZONE_Y = this.HEIGHT - 100;
        this.HIT_TOLERANCE = 50; // Forgiving hit detection window
        
        // Game state
        this.score = 1; // Starting from 1, no negative scores
        this.combo = 0;
        this.comboMultiplier = 1;
        this.notes = [];
        this.particles = [];
        this.isPlaying = false;
        this.lastTime = 0;
        this.audioStartTime = 0;
        
        // Performance monitoring
        this.fps = 60;
        this.frameCount = 0;
        this.lastFpsTime = 0;
        this.qualityMode = 'high'; // high, medium, low
        
        // Visual effects
        this.backgroundType = 'spectrum'; // spectrum, waves, particles
        this.glowIntensity = 1.0;
        
        // Settings with JSON persistence
        this.settings = this.loadSettings();
        
        // Object pooling for particles
        this.particlePool = [];
        for (let i = 0; i < 100; i++) {
            this.particlePool.push(this.createParticle());
        }
        
        this.initEventListeners();
        this.startGameLoop();
    }

    // Settings management with JSON persistence
    loadSettings() {
        try {
            const saved = localStorage.getItem('rhythmGameSettings');
            return saved ? JSON.parse(saved) : {
                resolution: { width: 800, height: 600 },
                fullscreen: false,
                performance: 'high',
                volume: 0.8,
                noteSpeed: 1.0,
                visualEffects: true
            };
        } catch (error) {
            console.warn('Failed to load settings:', error);
            return this.getDefaultSettings();
        }
    }

    saveSettings() {
        try {
            localStorage.setItem('rhythmGameSettings', JSON.stringify(this.settings));
        } catch (error) {
            console.warn('Failed to save settings:', error);
        }
    }

    getDefaultSettings() {
        return {
            resolution: { width: 800, height: 600 },
            fullscreen: false,
            performance: 'high',
            volume: 0.8,
            noteSpeed: 1.0,
            visualEffects: true
        };
    }

    // Event listeners with comprehensive error handling
    initEventListeners() {
        try {
            // File input for audio
            document.getElementById('audioFile').addEventListener('change', (e) => {
                this.handleAudioFile(e.target.files[0]);
            });

            // Play/Pause controls
            document.getElementById('playBtn').addEventListener('click', () => {
                this.playAudio();
            });

            document.getElementById('pauseBtn').addEventListener('click', () => {
                this.pauseAudio();
            });

            // Background mode selector
            document.getElementById('backgroundMode').addEventListener('change', (e) => {
                this.backgroundType = e.target.value;
                this.settings.backgroundType = e.target.value;
                this.saveSettings();
            });

            // Keyboard controls for hitting notes
            document.addEventListener('keydown', (e) => {
                if (e.code === 'Space' || e.code === 'Enter') {
                    e.preventDefault();
                    this.hitNote();
                }
            });

            // Mouse/touch controls for hitting notes
            this.canvas.addEventListener('click', () => {
                this.hitNote();
            });

            // Resize handling
            window.addEventListener('resize', () => {
                this.handleResize();
            });

        } catch (error) {
            console.error('Failed to initialize event listeners:', error);
        }
    }

    // Audio file handling with multiple format support and error recovery
    async handleAudioFile(file) {
        if (!file) return;

        try {
            // Validate file type
            const supportedTypes = ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/m4a'];
            if (!supportedTypes.includes(file.type) && 
                !file.name.match(/\.(mp3|wav|ogg|m4a)$/i)) {
                throw new Error('Unsupported audio format');
            }

            const url = URL.createObjectURL(file);
            this.audio.src = url;
            
            // Wait for audio to load
            await new Promise((resolve, reject) => {
                this.audio.onloadeddata = resolve;
                this.audio.onerror = reject;
                setTimeout(() => reject(new Error('Audio load timeout')), 10000);
            });

            this.generateNotes(file.name);
            this.updateUI(`Loaded: ${file.name}`);

        } catch (error) {
            console.error('Audio loading failed:', error);
            this.showErrorMessage(`Failed to load audio: ${error.message}`);
            // Graceful fallback - generate demo notes
            this.generateDemoNotes();
        }
    }

    // Smart chart generation with musical note patterns
    generateNotes(songName) {
        this.notes = [];
        const duration = this.audio.duration || 30; // Fallback duration
        const bpm = this.estimateBPM(songName); // Estimate BPM from song characteristics
        const beatInterval = 60 / bpm;
        
        // Generate notes based on musical patterns
        for (let time = 2; time < duration - 2; time += beatInterval) {
            // Add variation based on song progression
            const intensity = this.calculateIntensity(time, duration);
            const noteCount = Math.floor(1 + intensity * 3);
            
            for (let i = 0; i < noteCount; i++) {
                const lane = Math.floor(Math.random() * 4); // 4 lanes
                this.notes.push({
                    time: time + (i * beatInterval / noteCount),
                    lane: lane,
                    hit: false,
                    y: -50,
                    glowPhase: Math.random() * Math.PI * 2
                });
            }
        }

        // Remove duplicate notes (within same time window and lane)
        this.removeDuplicateNotes();
    }

    // Duplicate song detection and removal
    removeDuplicateNotes() {
        const processed = [];
        const timeThreshold = 0.1; // 100ms threshold
        
        this.notes.forEach(note => {
            const duplicate = processed.find(p => 
                Math.abs(p.time - note.time) < timeThreshold && p.lane === note.lane
            );
            
            if (!duplicate) {
                processed.push(note);
            }
        });
        
        this.notes = processed.sort((a, b) => a.time - b.time);
    }

    // Estimate BPM based on song characteristics
    estimateBPM(songName) {
        // Simple heuristic based on file name or default to 120 BPM
        const name = songName.toLowerCase();
        if (name.includes('slow') || name.includes('ballad')) return 80;
        if (name.includes('fast') || name.includes('techno')) return 140;
        if (name.includes('dance') || name.includes('electronic')) return 128;
        return 120; // Default BPM
    }

    // Calculate song intensity for progressive difficulty
    calculateIntensity(currentTime, totalDuration) {
        const progress = currentTime / totalDuration;
        // Intensity curve: start low, peak in middle, slightly lower at end
        return Math.sin(progress * Math.PI) * 0.8 + 0.2;
    }

    // Generate demo notes when audio fails to load
    generateDemoNotes() {
        this.notes = [];
        // Generate notes with shorter intervals for better demo experience
        for (let i = 0; i < 30; i++) {
            this.notes.push({
                time: i * 1.5, // Every 1.5 seconds instead of 2
                lane: Math.floor(Math.random() * 4),
                hit: false,
                y: -50,
                glowPhase: Math.random() * Math.PI * 2
            });
        }
        this.updateUI('Demo mode - Click or press Space to hit notes');
    }

    // Audio playback with error handling
    async playAudio() {
        try {
            if (this.audio.src) {
                await this.audio.play();
                this.isPlaying = true;
                this.audioStartTime = performance.now();
            } else {
                this.isPlaying = true; // Demo mode
                this.audioStartTime = performance.now();
            }
        } catch (error) {
            console.error('Playback failed:', error);
            this.showErrorMessage('Playback failed - continuing in demo mode');
            this.isPlaying = true; // Continue in demo mode
            this.audioStartTime = performance.now();
        }
    }

    pauseAudio() {
        try {
            if (this.audio.src) {
                this.audio.pause();
            }
            this.isPlaying = false;
        } catch (error) {
            console.error('Pause failed:', error);
        }
    }

    // Note hitting with enhanced timing and combo system
    hitNote() {
        if (!this.isPlaying) return;

        const currentTime = this.getCurrentTime();
        let bestNote = null;
        let bestDistance = Infinity;

        // Find the closest note in hit zone
        this.notes.forEach(note => {
            if (!note.hit && note.y > this.HIT_ZONE_Y - this.HIT_TOLERANCE && 
                note.y < this.HIT_ZONE_Y + this.HIT_TOLERANCE) {
                const distance = Math.abs(note.y - this.HIT_ZONE_Y);
                if (distance < bestDistance) {
                    bestDistance = distance;
                    bestNote = note;
                }
            }
        });

        if (bestNote && bestDistance <= this.HIT_TOLERANCE) {
            bestNote.hit = true;
            this.combo++;
            
            // Progressive combo multipliers (2x/3x/4x)
            if (this.combo >= 50) this.comboMultiplier = 4;
            else if (this.combo >= 20) this.comboMultiplier = 3;
            else if (this.combo >= 10) this.comboMultiplier = 2;
            else this.comboMultiplier = 1;

            // Scoring system starting from 1
            const baseScore = Math.max(1, Math.floor((this.HIT_TOLERANCE - bestDistance) * 2));
            this.score += baseScore * this.comboMultiplier;

            // Create hit effect particles
            this.createHitEffect(bestNote);
            
            this.updateUI();
        } else {
            // Miss - reset combo but don't subtract score
            this.combo = 0;
            this.comboMultiplier = 1;
            this.updateUI();
        }
    }

    // Performance-optimized particle system with object pooling
    createHitEffect(note) {
        const particleCount = this.settings.visualEffects ? 
            (this.qualityMode === 'high' ? 15 : this.qualityMode === 'medium' ? 8 : 5) : 0;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = this.getPooledParticle();
            if (particle) {
                particle.x = (note.lane + 0.5) * (this.WIDTH / 4);
                particle.y = note.y;
                particle.vx = (Math.random() - 0.5) * 8;
                particle.vy = (Math.random() - 0.5) * 8 - 2;
                particle.life = 1.0;
                particle.decay = 0.02;
                particle.color = `hsl(${180 + note.lane * 60}, 100%, 70%)`;
                particle.active = true;
            }
        }
    }

    getPooledParticle() {
        return this.particlePool.find(p => !p.active);
    }

    createParticle() {
        return {
            x: 0, y: 0, vx: 0, vy: 0,
            life: 0, decay: 0.02,
            color: '#fff',
            active: false
        };
    }

    // Game loop with frame-rate independent timing
    startGameLoop() {
        const loop = (timestamp) => {
            const deltaTime = timestamp - this.lastTime;
            this.lastTime = timestamp;
            
            this.update(deltaTime);
            this.render();
            
            // Performance monitoring
            this.frameCount++;
            if (timestamp - this.lastFpsTime > 1000) {
                this.fps = this.frameCount;
                this.frameCount = 0;
                this.lastFpsTime = timestamp;
                this.adjustQuality();
            }
            
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }

    // Performance monitoring with automatic quality adjustment
    adjustQuality() {
        if (this.fps < 45 && this.qualityMode === 'high') {
            this.qualityMode = 'medium';
            console.log('Quality adjusted to medium');
        } else if (this.fps < 30 && this.qualityMode === 'medium') {
            this.qualityMode = 'low';
            console.log('Quality adjusted to low');
        } else if (this.fps > 55 && this.qualityMode === 'low') {
            this.qualityMode = 'medium';
        } else if (this.fps > 58 && this.qualityMode === 'medium') {
            this.qualityMode = 'high';
        }
    }

    update(deltaTime) {
        if (!this.isPlaying) return;

        const currentTime = this.getCurrentTime();
        
        // Update note positions with smooth, frame-rate independent movement
        this.notes.forEach(note => {
            if (!note.hit && note.time <= currentTime + 3) { // 3 second lookahead
                const targetY = this.HIT_ZONE_Y + (note.time - currentTime) * 100 * this.NOTE_SPEED;
                note.y = targetY;
                note.glowPhase += deltaTime * 0.005;
            }
        });

        // Update particles with efficient pooling
        this.particles.forEach(particle => {
            if (particle.active) {
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.life -= particle.decay;
                
                if (particle.life <= 0) {
                    particle.active = false;
                }
            }
        });

        // Remove notes that are too far off screen (memory management)
        this.notes = this.notes.filter(note => note.y < this.HEIGHT + 100 && !note.hit);
    }

    getCurrentTime() {
        if (this.audio.src && !this.audio.paused) {
            return this.audio.currentTime;
        }
        // Demo mode timing
        return (performance.now() - this.audioStartTime) / 1000;
    }

    // Optimized rendering with reduced blitting operations
    render() {
        // Clear canvas efficiently
        this.ctx.fillStyle = 'rgba(10, 10, 26, 0.3)';
        this.ctx.fillRect(0, 0, this.WIDTH, this.HEIGHT);

        // Render dynamic background based on performance
        this.renderBackground();

        // Render hit zone with neon effect
        this.renderHitZone();

        // Render notes with optimized neon glow
        this.renderNotes();

        // Render particles
        this.renderParticles();

        // Render UI elements
        this.renderUI();
    }

    // Multiple dynamic backgrounds that scale with performance
    renderBackground() {
        const opacity = this.qualityMode === 'high' ? 0.6 : this.qualityMode === 'medium' ? 0.4 : 0.2;
        
        switch (this.backgroundType) {
            case 'spectrum':
                this.renderSpectrumBackground(opacity);
                break;
            case 'waves':
                this.renderWaveBackground(opacity);
                break;
            case 'particles':
                this.renderParticleBackground(opacity);
                break;
        }
    }

    renderSpectrumBackground(opacity) {
        const time = performance.now() * 0.001;
        const bars = this.qualityMode === 'high' ? 50 : this.qualityMode === 'medium' ? 25 : 15;
        
        for (let i = 0; i < bars; i++) {
            const x = (i / bars) * this.WIDTH;
            const height = Math.sin(time + i * 0.2) * 30 + 40;
            const hue = (i * 7 + time * 50) % 360;
            
            this.ctx.fillStyle = `hsla(${hue}, 80%, 60%, ${opacity})`;
            this.ctx.fillRect(x, this.HEIGHT - height, this.WIDTH / bars, height);
        }
    }

    renderWaveBackground(opacity) {
        const time = performance.now() * 0.001;
        this.ctx.strokeStyle = `rgba(0, 255, 255, ${opacity})`;
        this.ctx.lineWidth = 2;
        
        for (let wave = 0; wave < 3; wave++) {
            this.ctx.beginPath();
            for (let x = 0; x <= this.WIDTH; x += 10) {
                const y = this.HEIGHT / 2 + Math.sin((x * 0.01) + time + wave) * (30 + wave * 20);
                if (x === 0) this.ctx.moveTo(x, y);
                else this.ctx.lineTo(x, y);
            }
            this.ctx.stroke();
        }
    }

    renderParticleBackground(opacity) {
        const time = performance.now() * 0.001;
        const particleCount = this.qualityMode === 'high' ? 20 : this.qualityMode === 'medium' ? 12 : 8;
        
        for (let i = 0; i < particleCount; i++) {
            const x = (Math.sin(time + i) * 200 + this.WIDTH / 2);
            const y = (Math.cos(time * 0.7 + i) * 100 + this.HEIGHT / 2);
            const size = Math.sin(time * 2 + i) * 3 + 5;
            
            this.ctx.fillStyle = `hsla(${(time * 50 + i * 30) % 360}, 80%, 70%, ${opacity})`;
            this.ctx.beginPath();
            this.ctx.arc(x, y, size, 0, Math.PI * 2);
            this.ctx.fill();
        }
    }

    renderHitZone() {
        // Hit zone indicator with neon glow
        this.ctx.strokeStyle = '#00ffff';
        this.ctx.lineWidth = 3;
        this.ctx.shadowBlur = 20;
        this.ctx.shadowColor = '#00ffff';
        
        this.ctx.beginPath();
        this.ctx.moveTo(0, this.HIT_ZONE_Y);
        this.ctx.lineTo(this.WIDTH, this.HIT_ZONE_Y);
        this.ctx.stroke();
        
        this.ctx.shadowBlur = 0;
    }

    // Optimized note rendering with cached glow effects
    renderNotes() {
        const currentTime = this.getCurrentTime();
        
        this.notes.forEach(note => {
            if (note.y > -50 && note.y < this.HEIGHT + 50 && !note.hit) {
                const x = (note.lane + 0.5) * (this.WIDTH / 4);
                const distance = Math.abs(note.y - this.HIT_ZONE_Y);
                const inZone = distance <= this.HIT_TOLERANCE;
                
                // Note color based on lane and hit zone
                const hue = note.lane * 90;
                const saturation = inZone ? 100 : 70;
                const lightness = inZone ? 80 : 60;
                const glow = Math.sin(note.glowPhase) * 0.3 + 0.7;
                
                // Enhanced glow effect for notes approaching hit zone
                let glowSize = 15;
                if (inZone) {
                    glowSize = 25 + Math.sin(note.glowPhase * 2) * 10;
                }
                
                // Optimized neon glow effect
                if (this.settings.visualEffects && this.qualityMode !== 'low') {
                    this.ctx.shadowBlur = glowSize * glow;
                    this.ctx.shadowColor = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                }
                
                this.ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
                this.ctx.beginPath();
                
                // Larger notes when in hit zone
                const noteSize = inZone ? 25 + Math.sin(note.glowPhase) * 5 : 20;
                this.ctx.arc(x, note.y, noteSize, 0, Math.PI * 2);
                this.ctx.fill();
                
                // Add note lane indicators
                if (this.qualityMode === 'high') {
                    this.ctx.shadowBlur = 5;
                    this.ctx.strokeStyle = `hsla(${hue}, 50%, 50%, 0.5)`;
                    this.ctx.lineWidth = 2;
                    this.ctx.beginPath();
                    this.ctx.moveTo(x, 0);
                    this.ctx.lineTo(x, this.HEIGHT);
                    this.ctx.stroke();
                }
                
                this.ctx.shadowBlur = 0;
            }
        });
    }

    renderParticles() {
        if (!this.settings.visualEffects) return;
        
        this.particles.forEach(particle => {
            if (particle.active) {
                const alpha = particle.life;
                this.ctx.fillStyle = particle.color.replace('70%', `70%, ${alpha}`);
                this.ctx.beginPath();
                this.ctx.arc(particle.x, particle.y, 3 * particle.life, 0, Math.PI * 2);
                this.ctx.fill();
            }
        });
    }

    renderUI() {
        // Performance indicator (FPS)
        if (this.qualityMode !== 'high') {
            this.ctx.fillStyle = '#ffff00';
            this.ctx.font = '14px monospace';
            this.ctx.fillText(`FPS: ${this.fps} | Quality: ${this.qualityMode}`, 10, 20);
        }
        
        // Debug: Show notes in hit zone
        const notesInZone = this.notes.filter(note => 
            !note.hit && 
            note.y > this.HIT_ZONE_Y - this.HIT_TOLERANCE && 
            note.y < this.HIT_ZONE_Y + this.HIT_TOLERANCE
        ).length;
        
        if (notesInZone > 0) {
            this.ctx.fillStyle = '#00ff00';
            this.ctx.font = 'bold 20px monospace';
            this.ctx.fillText(`HIT NOW! (${notesInZone} notes)`, 10, 60);
        }
        
        // Combo visual feedback
        if (this.combo >= 10) {
            const comboGlow = Math.sin(performance.now() * 0.01) * 0.5 + 0.5;
            this.ctx.fillStyle = `rgba(255, 255, 0, ${0.3 + comboGlow * 0.4})`;
            this.ctx.font = 'bold 48px monospace';
            this.ctx.textAlign = 'center';
            
            let comboText = '';
            if (this.comboMultiplier === 4) comboText = '4X COMBO!';
            else if (this.comboMultiplier === 3) comboText = '3X COMBO!';
            else if (this.comboMultiplier === 2) comboText = '2X COMBO!';
            
            if (comboText) {
                this.ctx.shadowBlur = 20;
                this.ctx.shadowColor = '#ffff00';
                this.ctx.fillText(comboText, this.WIDTH / 2, 100);
                this.ctx.shadowBlur = 0;
            }
            
            this.ctx.textAlign = 'start';
        }
    }

    updateUI(message) {
        document.getElementById('score').textContent = `Score: ${this.score}`;
        document.getElementById('combo').textContent = `Combo: ${this.combo}x`;
        
        if (message) {
            console.log(message);
        }
    }

    showErrorMessage(message) {
        console.error(message);
        // Could add visual error display here
    }

    handleResize() {
        // Handle window resize for better UI scaling
        const container = document.querySelector('.game-container');
        const scale = Math.min(window.innerWidth / 800, window.innerHeight / 700);
        
        if (scale < 1) {
            container.style.transform = `scale(${scale})`;
        } else {
            container.style.transform = 'scale(1)';
        }
    }
}

// Initialize the game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.rhythmGame = new RhythmGame();
    } catch (error) {
        console.error('Failed to initialize rhythm game:', error);
        document.body.innerHTML = '<h1>Game initialization failed. Please refresh the page.</h1>';
    }
});
