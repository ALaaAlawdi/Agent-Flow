#!/bin/bash
# Agent-Flow Production Deploy
set -e

echo "🚀 Agent-Flow Production Deploy"
echo "==============================="
echo ""

# 1. Check env
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ DEEPSEEK_API_KEY not set"
    exit 1
fi
echo "✅ DeepSeek API key: SET"

# 2. Build & Run
echo ""
echo "🐳 Building containers..."
docker compose build --quiet

echo "🐳 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for health check..."
sleep 5
for i in 1 2 3 4 5; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy"
        break
    fi
    sleep 3
done

# 3. Show status
echo ""
echo "📊 Production Status:"
echo "   API:  http://localhost:8000"
echo "   UI:   http://localhost:3000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "📦 Services:"
docker compose ps

echo ""
echo "✅ Agent-Flow Deployed!"