const createProxyMiddleware = require("http-proxy-middleware");
module.exports = function(app) {
    app.use(createProxyMiddleware('/get_report/', 
        { target: 'http://127.0.0.1:5002/' }
    ));
    app.use(createProxyMiddleware('/get_data/', 
    { target: 'http://127.0.0.1:5021/' }
    ));
    app.use(createProxyMiddleware('/get_exclusions', 
    { target: 'http://127.0.0.1:5001/' }
    ));
    app.use(createProxyMiddleware('/get_track_status', 
    { target: 'http://127.0.0.1:5001/' }
    ));
    app.use(createProxyMiddleware('/track', 
    { target: 'http://127.0.0.1:5001/' }
    ));

}