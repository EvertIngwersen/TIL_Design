using System;
using System.Windows.Forms;
using System.Drawing;

namespace RailRouteGUI
{
    partial class Form1
    {
        // Designer variables
        private System.ComponentModel.IContainer components = null;
        private TextBox txtOrigin;
        private TextBox txtVia;
        private TextBox txtDestination;
        private Button btnCalculate;
        private Label lblResult;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            // Initialize the container first
            components = new System.ComponentModel.Container();

            // Form properties
            this.ClientSize = new Size(800, 600);
            this.Text = "Scandinavia Rail Route Planner";
            this.AutoScaleMode = AutoScaleMode.Font;

            // Origin TextBox
            txtOrigin = new TextBox();
            txtOrigin.Location = new Point(20, 20);
            txtOrigin.Size = new Size(200, 22);
            txtOrigin.PlaceholderText = "Origin City";
            this.Controls.Add(txtOrigin);

            // Via TextBox
            txtVia = new TextBox();
            txtVia.Location = new Point(20, 60);
            txtVia.Size = new Size(200, 22);
            txtVia.PlaceholderText = "Via (comma-separated)";
            this.Controls.Add(txtVia);

            // Destination TextBox
            txtDestination = new TextBox();
            txtDestination.Location = new Point(20, 100);
            txtDestination.Size = new Size(200, 22);
            txtDestination.PlaceholderText = "Destination City";
            this.Controls.Add(txtDestination);

            // Calculate Button
            btnCalculate = new Button();
            btnCalculate.Location = new Point(20, 140);
            btnCalculate.Size = new Size(200, 30);
            btnCalculate.Text = "Calculate Route";
            btnCalculate.Click += new EventHandler(this.btnCalculate_Click);
            this.Controls.Add(btnCalculate);

            // Result Label
            lblResult = new Label();
            lblResult.Location = new Point(20, 190);
            lblResult.Size = new Size(740, 360);
            lblResult.AutoSize = false;
            lblResult.Text = "Route summary will appear here";
            lblResult.BorderStyle = BorderStyle.FixedSingle;
            lblResult.BackColor = Color.White;
            lblResult.Padding = new Padding(5);
            lblResult.Font = new Font("Segoe UI", 9);
            lblResult.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom;
            this.Controls.Add(lblResult);
        }

        #endregion
    }
}