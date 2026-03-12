using System;
using System.Windows.Forms;

namespace RailRouteGUI
{
    static class Program
    {
        [STAThread] // This is necessary for WinForms
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new Form1());
        }
    }
}