// static/js/sw.js یا static/sw.js

self.addEventListener('install', (event) => {
    console.log('SW v3: installed');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('SW v3: activated');
});

// دریافت Push
self.addEventListener('push', (event) => {
    console.log('SW v3: push event received');

    let title = 'اعلان جدید';
    let body = '';
    let url = '/';  // اگر از سرور url نیاد، پیش‌فرض صفحه اصلی

    if (event.data) {
        // سعی می‌کنیم JSON باشه
        const raw = event.data.text();
        console.log('SW v3: raw push payload =', raw);

        try {
            const json = JSON.parse(raw);
            console.log('SW v3: parsed JSON payload', json);

            title = json.title || title;
            body = json.body || body;
            if (json.url) {
                url = json.url;
            }
        } catch (e) {
            console.log('SW v3: payload is plain text, not JSON');
            body = raw;
        }
    }

    const options = {
        body: body,
        icon: '/static/images/icon.png',   // اگر آیکون دیگری داری مسیرش رو عوض کن
        data: {
            url: url
        }
    };

    event.waitUntil(
        (async () => {
            console.log('SW v3: calling showNotification with:', { title, body, url });
            await self.registration.showNotification(title, options);
            console.log('SW v3: showNotification resolved');
        })()
    );
});

// کلیک روی نوتیفیکیشن
self.addEventListener('notificationclick', (event) => {
    console.log('SW v3: notification click', event.notification);

    event.notification.close();

    const targetUrl =
        event.notification &&
        event.notification.data &&
        event.notification.data.url
            ? event.notification.data.url
            : '/';

    event.waitUntil(
        (async () => {
            const allClients = await clients.matchAll({
                type: 'window',
                includeUncontrolled: true
            });

            // اگر تب/پنجره‌ای با همین URL بازه → فوکوس کن
            for (const client of allClients) {
                if (client.url === targetUrl && 'focus' in client) {
                    console.log('SW v3: focusing existing client', targetUrl);
                    return client.focus();
                }
            }

            // وگرنه → یک پنجره/تب جدید باز کن (در PWA یعنی اپ باز میشه)
            if (clients.openWindow) {
                console.log('SW v3: opening new window', targetUrl);
                return clients.openWindow(targetUrl);
            }
        })()
    );
});
