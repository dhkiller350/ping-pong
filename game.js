const canvas = document.getElementById('pong');
const ctx = canvas.getContext('2d');

// Game constants
const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const PADDLE_WIDTH = 16;
const PADDLE_HEIGHT = 100;
const BALL_SIZE = 16;

// Paddles
let playerY = (HEIGHT - PADDLE_HEIGHT) / 2;
let aiY = (HEIGHT - PADDLE_HEIGHT) / 2;

// Ball
let ballX = WIDTH / 2 - BALL_SIZE / 2;
let ballY = HEIGHT / 2 - BALL_SIZE / 2;
let ballSpeedX = 5;
let ballSpeedY = 3;

// Score
let playerScore = 0;
let aiScore = 0;

// Mouse control for player paddle
canvas.addEventListener('mousemove', function(e) {
    const rect = canvas.getBoundingClientRect();
    const mouseY = e.clientY - rect.top;
    playerY = mouseY - PADDLE_HEIGHT / 2;
    // Clamp paddle within bounds
    playerY = Math.max(0, Math.min(HEIGHT - PADDLE_HEIGHT, playerY));
});

// Draw everything
function draw() {
    // Clear
    ctx.clearRect(0, 0, WIDTH, HEIGHT);

    // Draw net
    ctx.strokeStyle = '#fff';
    ctx.setLineDash([8, 16]);
    ctx.beginPath();
    ctx.moveTo(WIDTH / 2, 0);
    ctx.lineTo(WIDTH / 2, HEIGHT);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw paddles
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, playerY, PADDLE_WIDTH, PADDLE_HEIGHT); // Player
    ctx.fillRect(WIDTH - PADDLE_WIDTH, aiY, PADDLE_WIDTH, PADDLE_HEIGHT); // AI

    // Draw ball
    ctx.fillRect(ballX, ballY, BALL_SIZE, BALL_SIZE);

    // Draw scores
    ctx.font = "32px Arial";
    ctx.fillStyle = "#fff";
    ctx.fillText(playerScore, WIDTH / 4, 40);
    ctx.fillText(aiScore, 3 * WIDTH / 4, 40);
}

// Update positions
function update() {
    // Ball movement
    ballX += ballSpeedX;
    ballY += ballSpeedY;

    // Top/bottom wall bounce
    if (ballY <= 0 || ballY + BALL_SIZE >= HEIGHT) {
        ballSpeedY *= -1;
        ballY = Math.max(0, Math.min(HEIGHT - BALL_SIZE, ballY));
    }

    // Left paddle collision
    if (
        ballX <= PADDLE_WIDTH &&
        ballY + BALL_SIZE > playerY &&
        ballY < playerY + PADDLE_HEIGHT
    ) {
        ballSpeedX *= -1;
        // Add a bit of vertical speed depending on hit position
        let hitPos = (ballY + BALL_SIZE / 2) - (playerY + PADDLE_HEIGHT / 2);
        ballSpeedY += hitPos * 0.08;
        ballX = PADDLE_WIDTH; // Prevent sticking
    }

    // Right paddle collision
    if (
        ballX + BALL_SIZE >= WIDTH - PADDLE_WIDTH &&
        ballY + BALL_SIZE > aiY &&
        ballY < aiY + PADDLE_HEIGHT
    ) {
        ballSpeedX *= -1;
        let hitPos = (ballY + BALL_SIZE / 2) - (aiY + PADDLE_HEIGHT / 2);
        ballSpeedY += hitPos * 0.08;
        ballX = WIDTH - PADDLE_WIDTH - BALL_SIZE;
    }

    // Score logic
    if (ballX < 0) {
        aiScore++;
        resetBall(-1);
    } else if (ballX > WIDTH) {
        playerScore++;
        resetBall(1);
    }

    // AI paddle follows ball
    let aiCenter = aiY + PADDLE_HEIGHT / 2;
    let ballCenter = ballY + BALL_SIZE / 2;
    // AI speed is limited
    let aiSpeed = 4;
    if (aiCenter < ballCenter - 10) {
        aiY += aiSpeed;
    } else if (aiCenter > ballCenter + 10) {
        aiY -= aiSpeed;
    }
    // Clamp AI paddle
    aiY = Math.max(0, Math.min(HEIGHT - PADDLE_HEIGHT, aiY));
}

// Reset ball after score
function resetBall(direction) {
    ballX = WIDTH / 2 - BALL_SIZE / 2;
    ballY = HEIGHT / 2 - BALL_SIZE / 2;
    ballSpeedX = 5 * direction;
    ballSpeedY = (Math.random() * 4 - 2);
}

// Main loop
function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
}

// Start the game
loop();
