# Get Telegram Chat ID Script
# Run this AFTER sending a message to your bot

$token = "8428672627:AAEzH0ejuM4J5-l35N6WQLaNI7G6vXaW3fE"

Write-Host "`nFetching updates from Telegram..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getUpdates"
    
    if ($response.result.Count -gt 0) {
        $chatId = $response.result[0].message.chat.id
        Write-Host "`n✅ SUCCESS! Your Chat ID is: $chatId" -ForegroundColor Green
        Write-Host "`n📝 Add this to your .env file:" -ForegroundColor Yellow
        Write-Host "TELEGRAM_CHAT_ID=$chatId" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "`n❌ No messages found in the response." -ForegroundColor Red
        Write-Host "`n📱 Please do the following:" -ForegroundColor Yellow
        Write-Host "1. Send a NEW message to your bot on Telegram" -ForegroundColor White
        Write-Host "2. Run this script again immediately" -ForegroundColor White
        Write-Host ""
    }
} catch {
    Write-Host "`n❌ Error: $_" -ForegroundColor Red
    Write-Host ""
}
