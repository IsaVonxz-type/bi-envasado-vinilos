param([string]$Salida)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Drawing, System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
Add-Type @"
using System; using System.Runtime.InteropServices;
public class M {
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
}
"@
[W]::SetProcessDPIAware() | Out-Null
New-Item -ItemType Directory -Force -Path $Salida | Out-Null

$p = Get-Process PBIDesktop | Select-Object -First 1
$h = $p.MainWindowHandle
[System.Windows.Forms.SendKeys]::SendWait('%')   # evita el bloqueo de primer plano
if ([W]::IsIconic($h)) { [W]::ShowWindow($h, 9) | Out-Null }   # solo si estaba minimizada; no tocar si ya está maximizada
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 1500
if ([W]::GetForegroundWindow() -ne $h) { Write-Output "AVISO: Power BI no quedó en primer plano"; }

$root = [System.Windows.Automation.AutomationElement]::FromHandle($h)
function Buscar($nombre, $minY, $tipo) {
  $todos = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
  foreach ($e in $todos) {
    $r = $e.Current.BoundingRectangle
    if ($e.Current.Name -eq $nombre -and $r.Y -gt $minY -and $tipo -contains $e.Current.ControlType.ProgrammaticName) { return $e }
  }
  return $null
}
function Pulsar($e) {
  if ($null -eq $e) { return $false }
  $r = $e.Current.BoundingRectangle
  if ($r.Width -le 0 -or [double]::IsInfinity($r.X)) { return $false }
  [M]::SetCursorPos([int]($r.X + $r.Width / 2), [int]($r.Y + $r.Height / 2)) | Out-Null
  Start-Sleep -Milliseconds 250
  [M]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero); Start-Sleep -Milliseconds 80
  [M]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
  return $true
}

# Plegar los paneles Visualizaciones y Datos (solo preferencia de la interfaz) y ajustar a la página
foreach ($panel in 'Visualizaciones', 'Datos') {
  $b = Buscar $panel 270 @('ControlType.Button')
  if ($b -and $b.Current.BoundingRectangle.Width -gt 150) { if (Pulsar $b) { Write-Output "Panel plegado: $panel"; Start-Sleep -Milliseconds 800 } }
}

$paginas = @(
  @{ n = 'Resumen ejecutivo'; f = 'pbi_01_resumen.png' },
  @{ n = 'Causas de paro';    f = 'pbi_02_paros.png' },
  @{ n = 'Confiabilidad';     f = 'pbi_03_confiabilidad.png' },
  @{ n = 'Capacidad';         f = 'pbi_04_capacidad.png' },
  @{ n = 'Calidad del dato';  f = 'pbi_05_calidad.png' }
)
foreach ($pg in $paginas) {
  $rv = New-Object W+RECT; [W]::GetWindowRect($h, [ref]$rv) | Out-Null
  $umbral = $rv.Top + 0.80 * ($rv.Bottom - $rv.Top)
  $tab = Buscar $pg.n $umbral @('ControlType.Button','ControlType.TabItem')
  if (-not (Pulsar $tab)) { Write-Output "No se pudo abrir la página $($pg.n)"; continue }
  Start-Sleep -Milliseconds 700
  $ajuste = Buscar 'Ajustar a la página' $umbral @('ControlType.Button')
  Pulsar $ajuste | Out-Null
  Start-Sleep -Milliseconds 5000   # que carguen los datos y se dibujen los visuales
  [M]::SetCursorPos(30, 900) | Out-Null   # fuera de la página, para que no salgan tooltips ni resaltados
  Start-Sleep -Milliseconds 1500
  $r = New-Object W+RECT; [W]::GetWindowRect($h, [ref]$r) | Out-Null
  $x = [Math]::Max(0, $r.Left); $y = [Math]::Max(0, $r.Top)
  $w = [Math]::Min($r.Right, [System.Windows.Forms.SystemInformation]::VirtualScreen.Width) - $x
  $al = [Math]::Min($r.Bottom, [System.Windows.Forms.SystemInformation]::VirtualScreen.Height) - $y
  $bmp = New-Object System.Drawing.Bitmap $w, $al
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($x, $y, 0, 0, $bmp.Size)
  $ruta = Join-Path $Salida $pg.f
  $bmp.Save($ruta, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
  Write-Output "Capturada $($pg.n): ${w}x${al}"
}
