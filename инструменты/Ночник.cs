// Ночник.exe — настоящее окно Windows (без браузера) на встроенном движке WebView2, на весь экран.
// Внутри exe зашито всё: страница, иконка, шрифты и библиотеки WebView2, поэтому интернет не нужен
// (только кнопке «Заполнить по расписанию»). Распаковка — в %LOCALAPPDATA%\Ночник, там же хранятся дневник и настройки.
// Если рядом с exe лежит Ночник.html, открывается он: правки в папке видны без пересборки.
// Собирается скриптом собрать_exe.py.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Ночник")]
[assembly: AssemblyDescription("Помощник перед сном")]
[assembly: AssemblyProduct("Ночник")]
[assembly: AssemblyCopyright("Гордеев А. А., 2026")]
[assembly: AssemblyVersion("2.0.0.0")]
[assembly: AssemblyFileVersion("2.0.0.0")]

static class Program
{
    public static string Home = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Ночник");
    public static string Bin = Path.Combine(Home, "bin");

    // sharp on every monitor: the window gets real pixels at each monitor's own scale (Per-Monitor V2),
    // otherwise Windows draws it at 100 % and stretches the picture, and at 150 % it looks blurry
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr v);
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern bool SetProcessDPIAware();

    [STAThread]                                   // WebView2 needs a single-threaded COM apartment
    static int Main()
    {
        try { if (!SetProcessDpiAwarenessContext(new IntPtr(-4))) SetProcessDPIAware(); } catch (Exception) { try { SetProcessDPIAware(); } catch (Exception) { } }
        bool first;
        using (var one = new Mutex(true, "Nochnik.App.Once", out first))
        {
            if (!first) { Bring(); return 0; }      // already open: show that window instead of a second one
            try
            {
                Directory.CreateDirectory(Bin);
                Save("WebView2Loader.dll", Path.Combine(Bin, "WebView2Loader.dll"));
                Save("Microsoft.Web.WebView2.Core.dll", Path.Combine(Bin, "Microsoft.Web.WebView2.Core.dll"));
                Save("Microsoft.Web.WebView2.WinForms.dll", Path.Combine(Bin, "Microsoft.Web.WebView2.WinForms.dll"));
                AppDomain.CurrentDomain.AssemblyResolve += (s, e) =>
                {
                    string f = Path.Combine(Bin, new AssemblyName(e.Name).Name + ".dll");
                    return File.Exists(f) ? Assembly.LoadFrom(f) : null;
                };
                string page = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Ночник.html");
                if (!File.Exists(page))
                {
                    page = Path.Combine(Home, "Ночник.html");
                    Save("page.html", page);
                    Save("icon.png", Path.Combine(Home, "icon.png"));
                }
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                return Run(page);
            }
            catch (Exception e)
            {
                MessageBox.Show("Не получилось открыть Ночник:\n" + e.Message, "Ночник", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return 1;
            }
        }
    }

    // kept apart so that WebView2 types are touched only after AssemblyResolve is in place
    [MethodImpl(MethodImplOptions.NoInlining)]
    static int Run(string page)
    {
        Application.Run(new NightWindow(page));
        return 0;
    }

    public static byte[] Res(string name)
    {
        using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(name))
        {
            if (s == null) return null;
            using (var m = new MemoryStream()) { s.CopyTo(m); return m.ToArray(); }
        }
    }

    // written only when different, so a running copy is never touched for nothing
    static void Save(string resource, string path)
    {
        byte[] data = Res(resource);
        if (File.Exists(path))
        {
            byte[] old = File.ReadAllBytes(path);
            if (old.Length == data.Length)
            {
                bool same = true;
                for (int i = 0; i < old.Length && same; i++) same = old[i] == data[i];
                if (same) return;
            }
        }
        File.WriteAllBytes(path, data);
    }

    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
    [System.Runtime.InteropServices.DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
    static void Bring()
    {
        foreach (Process p in Process.GetProcessesByName(Process.GetCurrentProcess().ProcessName))
            if (p.Id != Process.GetCurrentProcess().Id && p.MainWindowHandle != IntPtr.Zero)
            { ShowWindow(p.MainWindowHandle, 9); SetForegroundWindow(p.MainWindowHandle); }
    }
}

class NightWindow : Form
{
    static readonly Color Night = Color.FromArgb(6, 9, 21);   // the page background: no white flash while it loads
    readonly string page;
    readonly Microsoft.Web.WebView2.WinForms.WebView2 web = new Microsoft.Web.WebView2.WinForms.WebView2();
    readonly Dictionary<string, string> fonts = new Dictionary<string, string>();
    Microsoft.Web.WebView2.Core.CoreWebView2Environment env;
    bool full;
    Rectangle windowed;

    public NightWindow(string page)
    {
        this.page = page;
        Text = "Ночник";
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        BackColor = Night;
        StartPosition = FormStartPosition.Manual;
        Rectangle wa = Screen.FromPoint(Cursor.Position).WorkingArea;
        int ww = wa.Width * 3 / 4, wh = wa.Height * 4 / 5;      // the window after F11: in screen pixels, so a share of the screen, not a fixed size
        windowed = new Rectangle(wa.X + (wa.Width - ww) / 2, wa.Y + (wa.Height - wh) / 2, ww, wh);
        Bounds = windowed;
        web.Dock = DockStyle.Fill;
        web.DefaultBackgroundColor = Night;
        Controls.Add(web);
        SetFull(true);
        foreach (string line in Encoding.UTF8.GetString(Program.Res("fonts/map.txt")).Split('\n'))
        {
            string[] kv = line.Trim().Split('\t');
            if (kv.Length == 2) fonts[kv[0]] = kv[1];
        }
        Load += async (s, e) =>
        {
            try
            {
                Microsoft.Web.WebView2.Core.CoreWebView2Environment.SetLoaderDllFolderPath(Program.Bin);
                var opt = new Microsoft.Web.WebView2.Core.CoreWebView2EnvironmentOptions("--autoplay-policy=no-user-gesture-required");
                env = await Microsoft.Web.WebView2.Core.CoreWebView2Environment.CreateAsync(null, Path.Combine(Program.Home, "data"), opt);
                await web.EnsureCoreWebView2Async(env);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Не нашёлся движок WebView2 (он входит в Windows 10/11).\n" + ex.Message, "Ночник", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                Close(); return;
            }
            var core = web.CoreWebView2;
            core.Settings.AreDevToolsEnabled = false;
            core.Settings.AreDefaultContextMenusEnabled = false;
            core.Settings.IsStatusBarEnabled = false;
            core.Settings.IsZoomControlEnabled = false;
            core.Settings.IsPinchZoomEnabled = false;                  // a touchpad pinch zooms the sky, not the page
            core.Settings.AreBrowserAcceleratorKeysEnabled = false;   // no Ctrl+R, Ctrl+P and the like: it is an app, not a browser
            core.DocumentTitleChanged += (a, b) => Text = string.IsNullOrEmpty(core.DocumentTitle) ? "Ночник" : core.DocumentTitle;
            core.WindowCloseRequested += (a, b) => Close();
            core.WebMessageReceived += (a, b) =>
            {
                string m = b.TryGetWebMessageAsString();
                if (m == "close") Close();
                else if (m == "f11") Toggle();
            };
            core.NewWindowRequested += (a, b) =>            // links that want a new window go to the usual browser
            {
                b.Handled = true;
                try { Process.Start(b.Uri); } catch (Exception) { }
            };
            // fonts: answered from inside the exe, so the app looks the same without internet
            core.AddWebResourceRequestedFilter("https://fonts.googleapis.com/*", Microsoft.Web.WebView2.Core.CoreWebView2WebResourceContext.All,
                Microsoft.Web.WebView2.Core.CoreWebView2WebResourceRequestSourceKinds.All);
            core.AddWebResourceRequestedFilter("https://fonts.gstatic.com/*", Microsoft.Web.WebView2.Core.CoreWebView2WebResourceContext.All,
                Microsoft.Web.WebView2.Core.CoreWebView2WebResourceRequestSourceKinds.All);
            core.WebResourceRequested += (a, b) =>
            {
                string url = b.Request.Uri;
                byte[] body; string type;
                if (url.StartsWith("https://fonts.googleapis.com/")) { body = Program.Res("fonts/fonts.css"); type = "text/css; charset=utf-8"; }
                else
                {
                    string f;
                    if (!fonts.TryGetValue(url, out f)) return;
                    body = Program.Res("fonts/" + f); type = "font/woff2";
                }
                if (body == null) return;
                b.Response = env.CreateWebResourceResponse(new MemoryStream(body), 200, "OK",
                    "Content-Type: " + type + "\r\nAccess-Control-Allow-Origin: *\r\nCache-Control: max-age=31536000");
            };
            core.Navigate(new Uri(page).AbsoluteUri + "?exe");   // a string: System.Uri would escape the ? of a file address
        };
    }

    // full screen = a borderless window over the whole monitor, taskbar included
    // F11 can arrive twice (from the page and from the window): one press, one switch
    DateTime lastToggle = DateTime.MinValue;
    void Toggle()
    {
        if ((DateTime.Now - lastToggle).TotalMilliseconds < 300) return;
        lastToggle = DateTime.Now; SetFull(!full);
    }

    void SetFull(bool on)
    {
        if (on == full && Visible) return;
        full = on;
        if (on)
        {
            if (FormBorderStyle != FormBorderStyle.None) windowed = Bounds;
            FormBorderStyle = FormBorderStyle.None;
            WindowState = FormWindowState.Normal;
            Bounds = Screen.FromRectangle(Bounds).Bounds;
        }
        else
        {
            FormBorderStyle = FormBorderStyle.Sizable;
            Bounds = windowed;
        }
    }

    protected override bool ProcessCmdKey(ref Message msg, Keys key)
    {
        if (key == Keys.F11) { Toggle(); return true; }
        return base.ProcessCmdKey(ref msg, key);
    }
}
