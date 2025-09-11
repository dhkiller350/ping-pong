#!/usr/bin/env python3
"""
Enhanced Neon Rhythm Game
A high-performance rhythm game with neon aesthetics, optimized for smooth gameplay
with slower note speeds and comprehensive error handling.
"""

import pygame
import sys
import os
import math
import random
import json
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import time

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rhythm_game.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Game constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 60

# Colors (neon theme)
NEON_CYAN = (0, 255, 255)
NEON_PINK = (255, 20, 147)
NEON_GREEN = (57, 255, 20)
NEON_YELLOW = (255, 255, 0)
NEON_PURPLE = (186, 85, 211)
DARK_BG = (10, 10, 15)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Note lanes
NUM_LANES = 4
LANE_WIDTH = WINDOW_WIDTH // NUM_LANES
LANE_COLORS = [NEON_PINK, NEON_GREEN, NEON_YELLOW, NEON_CYAN]

# Gameplay settings (optimized for slower speeds)
NOTE_SPEED = 2.5  # 25% of original speed for better vocal sync
HIT_ZONE_Y = WINDOW_HEIGHT - 100
HIT_TOLERANCE = 50  # Forgiving hit detection
COMBO_MULTIPLIERS = [1, 2, 3, 4]  # Progressive multipliers

@dataclass
class Note:
    """Represents a musical note in the game"""
    lane: int
    y: float
    hit: bool = False
    missed: bool = False
    
class Particle:
    """Visual effect particle"""
    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -2)
        self.color = color
        self.life = 60
        self.max_life = 60
    
    def update(self) -> bool:
        """Update particle and return True if still alive"""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # gravity
        self.life -= 1
        return self.life > 0
    
    def draw(self, screen: pygame.Surface):
        """Draw the particle"""
        alpha = int(255 * (self.life / self.max_life))
        color = (*self.color, alpha)
        try:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)
        except Exception:
            pass  # Skip drawing if coordinates are invalid

class PerformanceMonitor:
    """Monitors game performance and adjusts quality"""
    def __init__(self):
        self.frame_times: List[float] = []
        self.quality_level = "high"  # high, medium, low
        self.last_adjustment = 0
        
    def update(self, dt: float):
        """Update performance monitoring"""
        self.frame_times.append(dt)
        if len(self.frame_times) > 60:  # Keep last 60 frames
            self.frame_times.pop(0)
            
        # Check if we need to adjust quality
        current_time = time.time()
        if current_time - self.last_adjustment > 2.0:  # Check every 2 seconds
            avg_fps = 1.0 / (sum(self.frame_times) / len(self.frame_times))
            if avg_fps < 45 and self.quality_level == "high":
                self.quality_level = "medium"
                self.last_adjustment = current_time
                logger.info("Performance adjusted to medium quality")
            elif avg_fps < 30 and self.quality_level == "medium":
                self.quality_level = "low"
                self.last_adjustment = current_time
                logger.info("Performance adjusted to low quality")
            elif avg_fps > 55 and self.quality_level == "medium":
                self.quality_level = "high"
                self.last_adjustment = current_time
                logger.info("Performance adjusted to high quality")

class BackgroundRenderer:
    """Handles dynamic background rendering"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.mode = "spectrum"  # spectrum, wave, particle
        self.time = 0
        self.spectrum_bars: List[float] = [0] * 32
        
    def update(self, dt: float):
        """Update background animations"""
        self.time += dt
        
        # Update spectrum bars with random values (simulated audio)
        for i in range(len(self.spectrum_bars)):
            target = random.uniform(0, 1) * 200
            self.spectrum_bars[i] += (target - self.spectrum_bars[i]) * 0.1
    
    def draw_spectrum(self, screen: pygame.Surface, quality: str):
        """Draw spectrum analyzer background"""
        bar_width = self.width // len(self.spectrum_bars)
        
        for i, height in enumerate(self.spectrum_bars):
            x = i * bar_width
            color_intensity = int(height / 200 * 255)
            color = (color_intensity, 50, 255 - color_intensity)
            
            if quality == "high":
                # Draw with glow effect
                for j in range(3):
                    alpha = 100 - j * 30
                    glow_rect = pygame.Rect(x - j, self.height - height - j, 
                                          bar_width + 2*j, height + 2*j)
                    pygame.draw.rect(screen, color, glow_rect)
            else:
                # Simple bars for better performance
                rect = pygame.Rect(x, self.height - height, bar_width, height)
                pygame.draw.rect(screen, color, rect)
    
    def draw_wave(self, screen: pygame.Surface, quality: str):
        """Draw wave background"""
        points = []
        wave_count = 3 if quality == "high" else 1
        
        for wave in range(wave_count):
            points.clear()
            for x in range(0, self.width, 5):
                y_offset = math.sin((x + self.time * 100 + wave * 50) * 0.01) * 30
                y = self.height // 2 + y_offset + wave * 20
                points.append((x, y))
            
            if len(points) > 1:
                color = (0, 200 - wave * 50, 255)
                try:
                    pygame.draw.lines(screen, color, False, points, 2)
                except ValueError:
                    pass  # Skip if points are invalid
    
    def draw(self, screen: pygame.Surface, quality: str):
        """Draw the current background"""
        if self.mode == "spectrum":
            self.draw_spectrum(screen, quality)
        elif self.mode == "wave":
            self.draw_wave(screen, quality)

class GameSettings:
    """Handles game settings persistence"""
    def __init__(self):
        self.settings_file = "settings.json"
        self.default_settings = {
            "resolution": [WINDOW_WIDTH, WINDOW_HEIGHT],
            "fullscreen": False,
            "note_speed": NOTE_SPEED,
            "audio_volume": 0.7,
            "performance_mode": "auto",
            "background_mode": "spectrum"
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    # Merge with defaults for missing keys
                    for key, value in self.default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

class AudioManager:
    """Handles audio loading and playback with error recovery"""
    def __init__(self):
        self.mixer_initialized = False
        self.supported_formats = ['.mp3', '.wav', '.ogg', '.m4a']
        self.current_music = None
        self.sound_effects = {}
        
    def initialize_mixer(self) -> bool:
        """Initialize pygame mixer with fallback options"""
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.mixer_initialized = True
            logger.info("Audio mixer initialized successfully")
            return True
        except pygame.error as e:
            logger.error(f"Failed to initialize audio mixer: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected audio initialization error: {e}")
            return False
    
    def load_music(self, file_path: str) -> bool:
        """Load music file with error handling"""
        if not self.mixer_initialized:
            if not self.initialize_mixer():
                return False
        
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Music file not found: {file_path}")
                return False
            
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"Unsupported audio format: {file_ext}")
                return False
            
            pygame.mixer.music.load(file_path)
            self.current_music = file_path
            logger.info(f"Loaded music: {file_path}")
            return True
            
        except pygame.error as e:
            logger.error(f"Failed to load music {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading music {file_path}: {e}")
            return False
    
    def play_music(self, loops: int = -1) -> bool:
        """Play loaded music with error handling"""
        if not self.mixer_initialized or not self.current_music:
            return False
        
        try:
            pygame.mixer.music.play(loops)
            logger.info("Music playback started")
            return True
        except pygame.error as e:
            logger.error(f"Failed to play music: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error playing music: {e}")
            return False

class RhythmGame:
    """Main game class"""
    def __init__(self):
        self.screen = None
        self.clock = None
        self.running = False
        self.settings = GameSettings()
        self.audio_manager = AudioManager()
        self.performance_monitor = PerformanceMonitor()
        self.background_renderer = None
        
        # Game state
        self.notes: List[Note] = []
        self.particles: List[Particle] = []
        self.score = 1  # Start at 1, never go negative
        self.combo = 0
        self.combo_multiplier = 1
        self.last_note_spawn = 0
        self.note_spawn_interval = 1000  # milliseconds
        
        # Fonts
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        # Initialize pygame
        self.init_pygame()
    
    def init_pygame(self) -> bool:
        """Initialize pygame with comprehensive error handling"""
        try:
            pygame.init()
            logger.info("Pygame initialized successfully")
            
            # Initialize fonts
            try:
                self.font_large = pygame.font.Font(None, 48)
                self.font_medium = pygame.font.Font(None, 32)
                self.font_small = pygame.font.Font(None, 24)
            except Exception as e:
                logger.warning(f"Font initialization failed: {e}")
                # Use system default font as fallback
                self.font_large = pygame.font.SysFont('arial', 48)
                self.font_medium = pygame.font.SysFont('arial', 32)
                self.font_small = pygame.font.SysFont('arial', 24)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pygame: {e}")
            return False
    
    def init_display(self) -> bool:
        """Initialize display with fallback handling"""
        try:
            # Get display settings
            width, height = self.settings.settings["resolution"]
            fullscreen = self.settings.settings["fullscreen"]
            
            # Set display mode with error handling
            if fullscreen:
                try:
                    # Try fullscreen mode first
                    self.screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
                    logger.info(f"Fullscreen mode initialized: {width}x{height}")
                except pygame.error as e:
                    logger.warning(f"Fullscreen mode failed: {e}, falling back to windowed")
                    # Fallback to windowed mode
                    self.screen = pygame.display.set_mode((width, height))
            else:
                self.screen = pygame.display.set_mode((width, height))
                logger.info(f"Windowed mode initialized: {width}x{height}")
            
            pygame.display.set_caption("Enhanced Neon Rhythm Game")
            
            # Initialize background renderer
            self.background_renderer = BackgroundRenderer(width, height)
            
            return True
            
        except pygame.error as e:
            logger.error(f"Display initialization failed: {e}")
            # Try with default resolution as last resort
            try:
                self.screen = pygame.display.set_mode((800, 600))
                self.background_renderer = BackgroundRenderer(800, 600)
                logger.info("Fallback display mode (800x600) initialized")
                return True
            except Exception as fallback_e:
                logger.error(f"All display initialization attempts failed: {fallback_e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected display error: {e}")
            return False
    
    def spawn_note(self):
        """Spawn a new note"""
        lane = random.randint(0, NUM_LANES - 1)
        note = Note(lane=lane, y=0)
        self.notes.append(note)
    
    def update_notes(self, dt: float):
        """Update note positions and handle collisions"""
        note_speed = self.settings.settings["note_speed"] * dt * 60  # Frame-rate independent
        
        for note in self.notes[:]:  # Create copy to safely modify during iteration
            if not note.hit and not note.missed:
                note.y += note_speed
                
                # Check if note missed
                if note.y > HIT_ZONE_Y + HIT_TOLERANCE:
                    note.missed = True
                    self.combo = 0  # Reset combo on miss
                    self.combo_multiplier = 1
    
    def handle_input(self):
        """Handle keyboard input for note hitting"""
        keys = pygame.key.get_pressed()
        
        # Map keys to lanes
        lane_keys = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
        
        for i, key in enumerate(lane_keys):
            if keys[key]:
                self.hit_note_in_lane(i)
    
    def hit_note_in_lane(self, lane: int):
        """Check for note hits in specified lane"""
        for note in self.notes:
            if (note.lane == lane and not note.hit and not note.missed and
                abs(note.y - HIT_ZONE_Y) <= HIT_TOLERANCE):
                
                note.hit = True
                self.combo += 1
                
                # Calculate combo multiplier
                if self.combo >= 30:
                    self.combo_multiplier = 4
                elif self.combo >= 20:
                    self.combo_multiplier = 3
                elif self.combo >= 10:
                    self.combo_multiplier = 2
                else:
                    self.combo_multiplier = 1
                
                # Add score (never negative)
                points = 100 * self.combo_multiplier
                self.score = max(1, self.score + points)
                
                # Spawn particles
                x = lane * LANE_WIDTH + LANE_WIDTH // 2
                for _ in range(8):
                    particle = Particle(x, HIT_ZONE_Y, LANE_COLORS[lane])
                    self.particles.append(particle)
                
                logger.debug(f"Note hit in lane {lane}, combo: {self.combo}, score: {self.score}")
                break
    
    def update_particles(self):
        """Update particle effects"""
        self.particles = [p for p in self.particles if p.update()]
    
    def draw_lanes(self):
        """Draw note lanes with neon effects"""
        quality = self.performance_monitor.quality_level
        
        for i in range(NUM_LANES):
            x = i * LANE_WIDTH
            
            # Lane separator
            if i > 0:
                pygame.draw.line(self.screen, WHITE, (x, 0), (x, WINDOW_HEIGHT), 2)
            
            # Hit zone with glow effect
            hit_zone_rect = pygame.Rect(x, HIT_ZONE_Y - 25, LANE_WIDTH, 50)
            
            if quality == "high":
                # Draw glow effect
                for j in range(3):
                    glow_color = (*LANE_COLORS[i], 100 - j * 30)
                    glow_rect = pygame.Rect(x - j, HIT_ZONE_Y - 25 - j, 
                                          LANE_WIDTH + 2*j, 50 + 2*j)
                    pygame.draw.rect(self.screen, LANE_COLORS[i], glow_rect, 2)
            
            pygame.draw.rect(self.screen, LANE_COLORS[i], hit_zone_rect, 3)
    
    def draw_notes(self):
        """Draw notes with enhanced visuals"""
        note_size = 30
        
        for note in self.notes:
            if note.hit or note.missed:
                continue
            
            x = note.lane * LANE_WIDTH + LANE_WIDTH // 2
            color = LANE_COLORS[note.lane]
            
            # Enhanced note visualization in hit zone
            if abs(note.y - HIT_ZONE_Y) <= HIT_TOLERANCE:
                note_size = 35
                # Add glow effect
                if self.performance_monitor.quality_level == "high":
                    pygame.draw.circle(self.screen, color, (int(x), int(note.y)), note_size + 5, 2)
            
            pygame.draw.circle(self.screen, color, (int(x), int(note.y)), note_size)
    
    def draw_ui(self):
        """Draw user interface"""
        # Score
        score_text = self.font_large.render(f"Score: {self.score}", True, NEON_CYAN)
        self.screen.blit(score_text, (10, 10))
        
        # Combo
        if self.combo > 5:
            combo_text = self.font_medium.render(f"Combo: {self.combo}x", True, NEON_YELLOW)
            text_rect = combo_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
            self.screen.blit(combo_text, text_rect)
        
        # Multiplier indicator
        if self.combo_multiplier > 1:
            multiplier_text = self.font_large.render(f"{self.combo_multiplier}x", True, NEON_PINK)
            text_rect = multiplier_text.get_rect(center=(WINDOW_WIDTH - 100, 50))
            self.screen.blit(multiplier_text, text_rect)
        
        # Performance info (debug)
        if len(self.performance_monitor.frame_times) > 0:
            avg_fps = 1.0 / (sum(self.performance_monitor.frame_times) / len(self.performance_monitor.frame_times))
            fps_text = self.font_small.render(f"FPS: {avg_fps:.1f} | Quality: {self.performance_monitor.quality_level}", True, WHITE)
            self.screen.blit(fps_text, (10, WINDOW_HEIGHT - 25))
    
    def draw_particles(self):
        """Draw particle effects"""
        for particle in self.particles:
            particle.draw(self.screen)
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Toggle background mode
                    modes = ["spectrum", "wave", "particle"]
                    current_idx = modes.index(self.background_renderer.mode)
                    next_idx = (current_idx + 1) % len(modes)
                    self.background_renderer.mode = modes[next_idx]
                    logger.info(f"Background mode changed to: {modes[next_idx]}")
    
    def update(self, dt: float):
        """Main update loop"""
        # Update performance monitoring
        self.performance_monitor.update(dt)
        
        # Spawn notes
        current_time = pygame.time.get_ticks()
        if current_time - self.last_note_spawn > self.note_spawn_interval:
            self.spawn_note()
            self.last_note_spawn = current_time
        
        # Update game objects
        self.update_notes(dt)
        self.update_particles()
        self.background_renderer.update(dt)
        
        # Handle input
        self.handle_input()
        
        # Remove old notes
        self.notes = [note for note in self.notes if note.y < WINDOW_HEIGHT + 100]
    
    def draw(self):
        """Main draw loop"""
        # Clear screen
        self.screen.fill(DARK_BG)
        
        # Draw background
        self.background_renderer.draw(self.screen, self.performance_monitor.quality_level)
        
        # Draw game elements
        self.draw_lanes()
        self.draw_notes()
        self.draw_particles()
        self.draw_ui()
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        if not self.init_display():
            logger.error("Failed to initialize display")
            return False
        
        # Initialize audio
        audio_initialized = self.audio_manager.initialize_mixer()
        if not audio_initialized:
            logger.warning("Audio system not available - running in demo mode")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        logger.info("Game loop starting")
        
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
                
                self.handle_events()
                self.update(dt)
                self.draw()
                
        except KeyboardInterrupt:
            logger.info("Game interrupted by user")
        except Exception as e:
            logger.error(f"Game loop error: {e}")
        finally:
            # Cleanup
            self.cleanup()
        
        return True
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.settings.save_settings()
            pygame.mixer.quit()
            pygame.quit()
            logger.info("Game cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def setup_display_fallbacks():
    """Setup display with comprehensive fallback handling"""
    try:
        # Try to get available display modes
        pygame.display.init()
        modes = pygame.display.list_modes()
        
        if not modes or modes == -1:
            logger.warning("No display modes available")
            return False
            
        logger.info(f"Available display modes: {len(modes) if modes != -1 else 'all'}")
        return True
        
    except pygame.error as e:
        logger.error(f"Display setup failed: {e}")
        return False

def main():
    """Main entry point with comprehensive error handling"""
    logger.info("Enhanced Neon Rhythm Game starting...")
    
    try:
        # Setup display with fallbacks
        if not setup_display_fallbacks():
            logger.error("Display setup failed - cannot continue")
            return 1
        
        # Create and run game
        game = RhythmGame()
        success = game.run()
        
        if success:
            logger.info("Game exited successfully")
            return 0
        else:
            logger.error("Game failed to start")
            return 1
            
    except pygame.error as e:
        logger.error(f"Pygame error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

class ChartGenerator:
    """Generates musical charts for songs"""
    def __init__(self):
        self.bpm = 120  # Default BPM
        self.time_signature = (4, 4)
        self.difficulty_levels = ["Easy", "Normal", "Hard", "Expert"]
        
    def analyze_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze audio file to extract musical features"""
        try:
            # Simulate audio analysis (would use librosa in real implementation)
            duration = 180  # 3 minutes default
            estimated_bpm = random.randint(80, 180)
            
            return {
                "duration": duration,
                "bpm": estimated_bpm,
                "energy_levels": [random.uniform(0.3, 1.0) for _ in range(int(duration))],
                "peak_times": [i * 4 for i in range(int(duration // 4))],  # Every 4 seconds
                "tempo_changes": []
            }
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return self.get_default_analysis()
    
    def get_default_analysis(self) -> Dict[str, Any]:
        """Return default analysis for when audio processing fails"""
        return {
            "duration": 180,
            "bpm": 120,
            "energy_levels": [0.7] * 180,
            "peak_times": [i * 2 for i in range(90)],
            "tempo_changes": []
        }
    
    def generate_chart(self, analysis: Dict[str, Any], difficulty: str) -> List[Dict[str, Any]]:
        """Generate note chart based on audio analysis"""
        notes = []
        duration = analysis["duration"]
        bpm = analysis["bpm"]
        energy_levels = analysis["energy_levels"]
        
        # Calculate note density based on difficulty
        density_multipliers = {
            "Easy": 0.3,
            "Normal": 0.6,
            "Hard": 0.9,
            "Expert": 1.2
        }
        
        base_density = density_multipliers.get(difficulty, 0.6)
        
        # Generate notes based on BPM and energy
        beat_interval = 60.0 / bpm  # seconds per beat
        current_time = 0
        
        while current_time < duration:
            # Determine if we should place a note based on energy and difficulty
            energy_index = min(int(current_time), len(energy_levels) - 1)
            energy = energy_levels[energy_index]
            
            note_probability = base_density * energy
            
            if random.random() < note_probability:
                # Choose lane based on musical patterns
                lane = self.choose_lane_musically(current_time, bpm, notes)
                
                notes.append({
                    "time": current_time,
                    "lane": lane,
                    "type": "normal",  # Could extend with hold notes, etc.
                    "energy": energy
                })
            
            # Advance time (varies based on difficulty and energy)
            time_advance = beat_interval * (0.5 + random.uniform(0, 0.5))
            if difficulty == "Expert":
                time_advance *= 0.7  # More frequent notes
            elif difficulty == "Easy":
                time_advance *= 1.5  # Less frequent notes
                
            current_time += time_advance
        
        # Remove notes that are too close together (duplicate prevention)
        return self.remove_duplicate_notes(notes)
    
    def choose_lane_musically(self, current_time: float, bpm: float, existing_notes: List[Dict[str, Any]]) -> int:
        """Choose lane based on musical patterns rather than pure randomness"""
        # Get recent notes to avoid immediate repetition
        recent_notes = [n for n in existing_notes if current_time - n["time"] < 2.0]
        recent_lanes = [n["lane"] for n in recent_notes[-4:]]  # Last 4 notes
        
        # Prefer lanes that haven't been used recently
        lane_weights = [1.0] * NUM_LANES
        for lane in recent_lanes:
            lane_weights[lane] *= 0.3
        
        # Add musical pattern preference (e.g., alternating patterns)
        if len(recent_notes) > 0:
            last_lane = recent_notes[-1]["lane"]
            # Encourage alternating patterns
            for i in range(NUM_LANES):
                if abs(i - last_lane) == 1 or abs(i - last_lane) == 3:  # Adjacent or opposite
                    lane_weights[i] *= 1.5
        
        # Choose lane based on weights
        total_weight = sum(lane_weights)
        if total_weight == 0:
            return random.randint(0, NUM_LANES - 1)
        
        rand_val = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(lane_weights):
            cumulative += weight
            if rand_val <= cumulative:
                return i
        
        return NUM_LANES - 1  # Fallback
    
    def remove_duplicate_notes(self, notes: List[Dict[str, Any]], min_gap: float = 0.1) -> List[Dict[str, Any]]:
        """Remove notes that are too close together in time"""
        if len(notes) <= 1:
            return notes
        
        # Sort by time
        notes.sort(key=lambda n: n["time"])
        
        filtered_notes = [notes[0]]  # Always keep first note
        
        for note in notes[1:]:
            # Check if this note is too close to the last kept note
            time_gap = note["time"] - filtered_notes[-1]["time"]
            
            if time_gap >= min_gap:
                # Also check if it's the same lane (avoid rapid repetition)
                if (time_gap >= min_gap * 2 or 
                    note["lane"] != filtered_notes[-1]["lane"]):
                    filtered_notes.append(note)
            
        return filtered_notes

class SongManager:
    """Manages song library and file scanning"""
    def __init__(self):
        self.song_directories = ["./music", "./songs", "~/Music"]
        self.supported_formats = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        self.song_cache = {}
        self.scan_errors = []
        
    def scan_for_songs(self) -> List[Dict[str, Any]]:
        """Scan directories for music files with error recovery"""
        songs = []
        self.scan_errors.clear()
        
        for directory in self.song_directories:
            try:
                expanded_dir = os.path.expanduser(directory)
                if not os.path.exists(expanded_dir):
                    logger.info(f"Music directory does not exist: {expanded_dir}")
                    continue
                
                songs.extend(self.scan_directory(expanded_dir))
                
            except PermissionError as e:
                error_msg = f"Permission denied accessing {directory}: {e}"
                logger.warning(error_msg)
                self.scan_errors.append(error_msg)
            except Exception as e:
                error_msg = f"Error scanning directory {directory}: {e}"
                logger.error(error_msg)
                self.scan_errors.append(error_msg)
        
        # Remove duplicates based on file name and size
        unique_songs = self.remove_duplicate_songs(songs)
        logger.info(f"Found {len(unique_songs)} unique songs (removed {len(songs) - len(unique_songs)} duplicates)")
        
        return unique_songs
    
    def scan_directory(self, directory: str) -> List[Dict[str, Any]]:
        """Scan a single directory for music files"""
        songs = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        if file_ext in self.supported_formats:
                            song_info = self.get_song_info(file_path)
                            if song_info:
                                songs.append(song_info)
                                
                    except Exception as e:
                        error_msg = f"Error processing file {file}: {e}"
                        logger.debug(error_msg)  # Debug level to avoid spam
                        self.scan_errors.append(error_msg)
        
        except Exception as e:
            logger.error(f"Error walking directory {directory}: {e}")
        
        return songs
    
    def get_song_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract song information from file"""
        try:
            # Check if file is accessible
            if not os.access(file_path, os.R_OK):
                return None
            
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            
            # Skip very small files (likely not music)
            if file_size < 1024 * 100:  # Less than 100KB
                return None
            
            song_info = {
                "path": file_path,
                "filename": os.path.basename(file_path),
                "title": os.path.splitext(os.path.basename(file_path))[0],
                "artist": "Unknown Artist",
                "album": "Unknown Album",
                "duration": 0,
                "size": file_size,
                "format": os.path.splitext(file_path)[1].lower()
            }
            
            # Try to extract metadata (would use mutagen in real implementation)
            try:
                # Simulate metadata extraction
                song_info["duration"] = random.randint(120, 300)  # 2-5 minutes
                
                # Extract artist and title from filename if formatted as "Artist - Title"
                filename_parts = song_info["title"].split(" - ", 1)
                if len(filename_parts) == 2:
                    song_info["artist"] = filename_parts[0].strip()
                    song_info["title"] = filename_parts[1].strip()
                
            except Exception as e:
                logger.debug(f"Metadata extraction failed for {file_path}: {e}")
            
            return song_info
            
        except Exception as e:
            logger.debug(f"Failed to get song info for {file_path}: {e}")
            return None
    
    def remove_duplicate_songs(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate songs based on filename and size"""
        seen_songs = set()
        unique_songs = []
        
        for song in songs:
            # Create identifier based on filename and size
            identifier = (song["filename"].lower(), song["size"])
            
            if identifier not in seen_songs:
                seen_songs.add(identifier)
                unique_songs.append(song)
        
        return unique_songs

class VisualEffectsManager:
    """Manages advanced visual effects and animations"""
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.effects = []
        self.background_particles = []
        self.screen_shake = {"intensity": 0, "duration": 0}
        
    def add_note_hit_effect(self, x: int, y: int, color: Tuple[int, int, int]):
        """Add visual effect when a note is hit"""
        # Explosion effect
        for i in range(12):
            angle = (i / 12) * 2 * math.pi
            speed = random.uniform(2, 6)
            particle = {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": color,
                "life": 30,
                "max_life": 30,
                "size": random.uniform(2, 5)
            }
            self.effects.append(particle)
        
        # Screen shake on good hits
        self.add_screen_shake(2, 5)
    
    def add_combo_effect(self, combo_count: int, x: int, y: int):
        """Add special effect for combo milestones"""
        if combo_count % 10 == 0:  # Every 10 combo
            # Radial burst effect
            for i in range(20):
                angle = (i / 20) * 2 * math.pi
                speed = random.uniform(3, 8)
                particle = {
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "color": NEON_YELLOW,
                    "life": 60,
                    "max_life": 60,
                    "size": random.uniform(3, 8),
                    "glow": True
                }
                self.effects.append(particle)
            
            # Stronger screen shake for combo milestones
            self.add_screen_shake(5, 10)
    
    def add_screen_shake(self, intensity: int, duration: int):
        """Add screen shake effect"""
        self.screen_shake["intensity"] = max(self.screen_shake["intensity"], intensity)
        self.screen_shake["duration"] = max(self.screen_shake["duration"], duration)
    
    def update_background_particles(self, quality: str):
        """Update floating background particles"""
        # Add new particles occasionally
        if random.random() < 0.02 and len(self.background_particles) < 50:
            particle = {
                "x": random.uniform(0, self.screen_width),
                "y": self.screen_height + 10,
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-1, -2),
                "color": random.choice([NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_YELLOW]),
                "life": random.randint(300, 600),
                "max_life": random.randint(300, 600),
                "size": random.uniform(1, 3),
                "alpha": random.uniform(0.3, 0.8)
            }
            self.background_particles.append(particle)
        
        # Update existing particles
        for particle in self.background_particles[:]:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1
            
            # Remove particles that are off-screen or dead
            if (particle["life"] <= 0 or 
                particle["y"] < -10 or 
                particle["x"] < -10 or 
                particle["x"] > self.screen_width + 10):
                self.background_particles.remove(particle)
    
    def update_effects(self):
        """Update all visual effects"""
        # Update hit effects
        for effect in self.effects[:]:
            effect["x"] += effect["vx"]
            effect["y"] += effect["vy"]
            effect["vy"] += 0.1  # gravity
            effect["life"] -= 1
            
            if effect["life"] <= 0:
                self.effects.remove(effect)
        
        # Update screen shake
        if self.screen_shake["duration"] > 0:
            self.screen_shake["duration"] -= 1
            if self.screen_shake["duration"] <= 0:
                self.screen_shake["intensity"] = 0
    
    def get_screen_offset(self) -> Tuple[int, int]:
        """Get screen shake offset"""
        if self.screen_shake["intensity"] > 0:
            offset_x = random.randint(-self.screen_shake["intensity"], self.screen_shake["intensity"])
            offset_y = random.randint(-self.screen_shake["intensity"], self.screen_shake["intensity"])
            return (offset_x, offset_y)
        return (0, 0)
    
    def draw_effects(self, screen: pygame.Surface, quality: str):
        """Draw all visual effects"""
        # Draw background particles
        for particle in self.background_particles:
            if quality == "high":
                # Draw with alpha blending
                alpha = int(255 * particle["alpha"] * (particle["life"] / particle["max_life"]))
                color = (*particle["color"], alpha)
            else:
                color = particle["color"]
            
            try:
                pygame.draw.circle(screen, color, 
                                 (int(particle["x"]), int(particle["y"])), 
                                 int(particle["size"]))
            except Exception:
                pass  # Skip invalid coordinates
        
        # Draw hit effects
        for effect in self.effects:
            alpha_factor = effect["life"] / effect["max_life"]
            color = effect["color"]
            
            if quality == "high" and effect.get("glow", False):
                # Draw glow effect
                for i in range(3):
                    glow_size = int(effect["size"] + i * 2)
                    glow_alpha = int(alpha_factor * 100 / (i + 1))
                    try:
                        pygame.draw.circle(screen, color,
                                         (int(effect["x"]), int(effect["y"])), 
                                         glow_size)
                    except Exception:
                        pass
            else:
                try:
                    pygame.draw.circle(screen, color,
                                     (int(effect["x"]), int(effect["y"])), 
                                     int(effect["size"] * alpha_factor))
                except Exception:
                    pass

class MenuSystem:
    """Handles game menus and UI navigation"""
    def __init__(self, screen: pygame.Surface, fonts: Dict[str, pygame.font.Font]):
        self.screen = screen
        self.fonts = fonts
        self.current_menu = "main"
        self.selected_option = 0
        self.menu_options = {
            "main": ["Play", "Song Selection", "Settings", "Exit"],
            "settings": ["Resolution", "Fullscreen", "Audio Volume", "Performance Mode", "Back"],
            "song_selection": []  # Populated dynamically
        }
        self.menu_animations = {}
        self.transition_progress = 0
    
    def handle_menu_input(self, event: pygame.event.Event) -> str:
        """Handle menu navigation input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.menu_options[self.current_menu])
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.menu_options[self.current_menu])
            elif event.key == pygame.K_RETURN:
                return self.activate_menu_option()
            elif event.key == pygame.K_ESCAPE:
                if self.current_menu == "main":
                    return "exit"
                else:
                    self.current_menu = "main"
                    self.selected_option = 0
        
        return "none"
    
    def activate_menu_option(self) -> str:
        """Activate the currently selected menu option"""
        options = self.menu_options[self.current_menu]
        if self.selected_option < len(options):
            selected = options[self.selected_option]
            
            if self.current_menu == "main":
                if selected == "Play":
                    return "start_game"
                elif selected == "Song Selection":
                    self.current_menu = "song_selection"
                    self.selected_option = 0
                elif selected == "Settings":
                    self.current_menu = "settings"
                    self.selected_option = 0
                elif selected == "Exit":
                    return "exit"
            elif self.current_menu == "settings":
                if selected == "Back":
                    self.current_menu = "main"
                    self.selected_option = 0
                else:
                    return f"setting_{selected.lower().replace(' ', '_')}"
            elif self.current_menu == "song_selection":
                if selected == "Back":
                    self.current_menu = "main"
                    self.selected_option = 0
                else:
                    return f"select_song_{self.selected_option}"
        
        return "none"
    
    def draw_menu(self):
        """Draw the current menu"""
        # Draw title
        title_text = ""
        if self.current_menu == "main":
            title_text = "NEON RHYTHM"
        elif self.current_menu == "settings":
            title_text = "SETTINGS"
        elif self.current_menu == "song_selection":
            title_text = "SELECT SONG"
        
        # Animated title with glow effect
        title_surface = self.fonts["large"].render(title_text, True, NEON_CYAN)
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        
        # Draw title glow
        for i in range(3):
            glow_surface = self.fonts["large"].render(title_text, True, NEON_CYAN)
            glow_rect = title_rect.copy()
            glow_rect.x += random.randint(-i, i)
            glow_rect.y += random.randint(-i, i)
            self.screen.blit(glow_surface, glow_rect)
        
        self.screen.blit(title_surface, title_rect)
        
        # Draw menu options
        options = self.menu_options[self.current_menu]
        start_y = 250
        option_height = 60
        
        for i, option in enumerate(options):
            color = NEON_PINK if i == self.selected_option else WHITE
            
            # Animate selected option
            offset_x = 0
            if i == self.selected_option:
                offset_x = int(math.sin(pygame.time.get_ticks() * 0.01) * 10)
            
            option_surface = self.fonts["medium"].render(option, True, color)
            option_rect = option_surface.get_rect(center=(self.screen.get_width() // 2 + offset_x, 
                                                         start_y + i * option_height))
            
            # Draw selection indicator
            if i == self.selected_option:
                indicator_points = [
                    (option_rect.left - 30, option_rect.centery),
                    (option_rect.left - 15, option_rect.centery - 10),
                    (option_rect.left - 15, option_rect.centery + 10)
                ]
                pygame.draw.polygon(self.screen, NEON_PINK, indicator_points)
            
            self.screen.blit(option_surface, option_rect)
        
        # Draw instructions
        instructions = [
            "Use UP/DOWN arrows to navigate",
            "Press ENTER to select",
            "Press ESC to go back"
        ]
        
        for i, instruction in enumerate(instructions):
            instruction_surface = self.fonts["small"].render(instruction, True, WHITE)
            instruction_rect = instruction_surface.get_rect(center=(self.screen.get_width() // 2, 
                                                                  self.screen.get_height() - 100 + i * 25))
            self.screen.blit(instruction_surface, instruction_rect)

class GameStateManager:
    """Manages different game states and transitions"""
    def __init__(self):
        self.current_state = "menu"  # menu, game, pause, game_over
        self.previous_state = "menu"
        self.state_transition_time = 0
        self.transition_duration = 500  # milliseconds
        
    def change_state(self, new_state: str):
        """Change to a new game state"""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            self.state_transition_time = pygame.time.get_ticks()
            logger.info(f"Game state changed from {self.previous_state} to {new_state}")
    
    def is_transitioning(self) -> bool:
        """Check if currently in a state transition"""
        return (pygame.time.get_ticks() - self.state_transition_time) < self.transition_duration
    
    def get_transition_progress(self) -> float:
        """Get transition progress (0.0 to 1.0)"""
        if not self.is_transitioning():
            return 1.0
        
        elapsed = pygame.time.get_ticks() - self.state_transition_time
        return min(1.0, elapsed / self.transition_duration)

class ConfigManager:
    """Handles configuration management with validation"""
    def __init__(self):
        self.config_file = "game_config.json"
        self.default_config = {
            "display": {
                "width": WINDOW_WIDTH,
                "height": WINDOW_HEIGHT,
                "fullscreen": False,
                "vsync": True
            },
            "audio": {
                "master_volume": 0.8,
                "music_volume": 0.7,
                "sfx_volume": 0.9,
                "audio_buffer": 512
            },
            "gameplay": {
                "note_speed_multiplier": 1.0,
                "hit_tolerance": HIT_TOLERANCE,
                "show_fps": False,
                "auto_play": False
            },
            "performance": {
                "quality_mode": "auto",  # auto, high, medium, low
                "particle_limit": 100,
                "effect_quality": "high",
                "background_complexity": "high"
            },
            "controls": {
                "lane_1": "d",
                "lane_2": "f", 
                "lane_3": "j",
                "lane_4": "k",
                "pause": "space",
                "menu": "escape"
            }
        }
        self.config = self.load_config()
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file with validation"""
        try:
            if os.path.exists(self.config_file):
                pass  # Placeholder
        except:
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.default_config.copy()
    
    def merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self.merge_configs(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate config values and fix invalid ones"""
        try:
            # Validate display settings
            if config["display"]["width"] < 800:
                config["display"]["width"] = 800
            if config["display"]["height"] < 600:
                config["display"]["height"] = 600
            
            # Validate audio settings
            for audio_key in ["master_volume", "music_volume", "sfx_volume"]:
                config["audio"][audio_key] = max(0.0, min(1.0, config["audio"][audio_key]))
            
            # Validate gameplay settings
            config["gameplay"]["note_speed_multiplier"] = max(0.1, min(3.0, config["gameplay"]["note_speed_multiplier"]))
            config["gameplay"]["hit_tolerance"] = max(10, min(100, config["gameplay"]["hit_tolerance"]))
            
            # Validate performance settings
            valid_quality_modes = ["auto", "high", "medium", "low"]
            if config["performance"]["quality_mode"] not in valid_quality_modes:
                config["performance"]["quality_mode"] = "auto"
            
            config["performance"]["particle_limit"] = max(10, min(500, config["performance"]["particle_limit"]))
            
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return self.default_config.copy()
        
        return config
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, section: str, key: str, default=None):
        """Get a configuration value"""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: str, value):
        """Set a configuration value"""
        try:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
        except Exception as e:
            logger.error(f"Failed to set config value: {e}")

def initialize_audio_system() -> bool:
    """Initialize audio system with comprehensive error handling"""
    try:
        # Try different audio drivers
        audio_drivers = ['alsa', 'pulse', 'oss', 'dsound', 'winmm']
        
        for driver in audio_drivers:
            try:
                os.environ['SDL_AUDIODRIVER'] = driver
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                logger.info(f"Audio initialized with {driver} driver")
                return True
            except pygame.error:
                continue
        
        # If all drivers fail, try with default settings
        try:
            pygame.mixer.init()
            logger.info("Audio initialized with default settings")
            return True
        except pygame.error as e:
            logger.error(f"All audio initialization attempts failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected audio initialization error: {e}")
        return False

def check_system_requirements() -> Dict[str, bool]:
    """Check if system meets minimum requirements"""
    requirements = {
        "pygame_available": True,
        "display_available": True,
        "audio_available": True,
        "sufficient_memory": True,
        "python_version": True
    }
    
    try:
        # Check Python version
        if sys.version_info < (3, 6):
            requirements["python_version"] = False
            logger.warning("Python 3.6+ required")
        
        # Check pygame
        try:
            import pygame
        except ImportError:
            requirements["pygame_available"] = False
            logger.error("Pygame not available")
        
        # Check display
        try:
            pygame.display.init()
            if not pygame.display.get_init():
                requirements["display_available"] = False
        except Exception:
            requirements["display_available"] = False
            logger.error("Display system not available")
        
        # Check audio
        requirements["audio_available"] = initialize_audio_system()
        
        # Check memory (basic check)
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.available < 100 * 1024 * 1024:  # 100MB
                requirements["sufficient_memory"] = False
        except ImportError:
            # psutil not available, assume memory is sufficient
            pass
        
    except Exception as e:
        logger.error(f"System requirements check failed: {e}")
    
    return requirements

def create_error_report(error: Exception, context: str) -> str:
    """Create detailed error report for debugging"""
    import traceback
    
    report = []
    report.append(f"=== ERROR REPORT ===")
    report.append(f"Context: {context}")
    report.append(f"Error Type: {type(error).__name__}")
    report.append(f"Error Message: {str(error)}")
    report.append(f"Python Version: {sys.version}")
    report.append(f"Pygame Version: {pygame.version.ver if 'pygame' in sys.modules else 'Not loaded'}")
    report.append(f"Platform: {sys.platform}")
    report.append(f"")
    report.append("Traceback:")
    report.append(traceback.format_exc())
    
    return "\n".join(report)

def safe_cleanup():
    """Safely cleanup all resources"""
    try:
        if pygame.get_init():
            pygame.mixer.quit()
            pygame.quit()
        logger.info("Safe cleanup completed")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def main():
    """Main entry point with comprehensive error handling"""
    logger.info("Enhanced Neon Rhythm Game starting...")
    
    try:
        # Check system requirements
        requirements = check_system_requirements()
        failed_requirements = [req for req, status in requirements.items() if not status]
        
        if failed_requirements:
            logger.error(f"System requirements not met: {failed_requirements}")
            print(f"System requirements not met: {failed_requirements}")
            return 1
        
        # Setup display with fallbacks
        if not setup_display_fallbacks():
            logger.error("Display setup failed - cannot continue")
            return 1
        
        # Create and run game
        game = RhythmGame()
        success = game.run()
        
        if success:
            logger.info("Game exited successfully")
            return 0
        else:
            logger.error("Game failed to start")
            return 1
            
    except pygame.error as e:
        error_report = create_error_report(e, "pygame_error")
        logger.error(error_report)
        return 1
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"Critical error: {e}")
        safe_cleanup()
        sys.exit(1)