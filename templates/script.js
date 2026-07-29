        // Desktop: switch sections
        document.querySelectorAll('.desktop-nav-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.desktop-nav-item').forEach(n => n.classList.remove('active'));
                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

                item.classList.add('active');
                document.getElementById(item.getAttribute('data-target')).classList.add('active');
            });
        });

        // Mobile: open panel
        document.querySelectorAll('.mobile-nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const panelId = 'panel-' + item.getAttribute('data-panel');
                document.getElementById(panelId).classList.add('active');
            });
        });

        // Mobile: back button
        document.querySelectorAll('.back-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mobile-panel').forEach(p => p.classList.remove('active'));
            });
        });
