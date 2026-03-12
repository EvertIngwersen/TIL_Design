using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace RailRouteGUI
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void btnCalculate_Click(object sender, EventArgs e)
        {
            string origin = txtOrigin.Text;
            string via = txtVia.Text;
            string destination = txtDestination.Text;

            if (string.IsNullOrWhiteSpace(origin) || string.IsNullOrWhiteSpace(destination))
            {
                lblResult.Text = "Please enter at least Origin and Destination.";
                return;
            }

            string pythonExe = @"C:\ProgramData\anaconda3\envs\DESIGN\python.exe";
            string scriptPath = @"C:\Users\evert\Documents\TU-Delft\TIL Master\TIL5050-20 TIL Design Project\TIL_Design_Repo\TIL_Design\Modeling\Rail_map_Scandinavia_GUI_edit.py";

            // Combine arguments: origin, via, destination
            string args = $"\"{scriptPath}\" \"{origin}\" \"{via}\" \"{destination}\"";

            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = args,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            };

            try
            {
                using (Process process = new Process { StartInfo = psi })
                {
                    process.Start();

                    string output = process.StandardOutput.ReadToEnd();
                    string errors = process.StandardError.ReadToEnd();

                    process.WaitForExit();

                    if (!string.IsNullOrEmpty(errors))
                    {
                        lblResult.Text = "Python error:\n" + errors;
                    }
                    else
                    {
                        lblResult.Text = output;
                    }
                }
            }
            catch (Exception ex)
            {
                lblResult.Text = "Error running Python:\n" + ex.Message;
            }
        }
    }
}