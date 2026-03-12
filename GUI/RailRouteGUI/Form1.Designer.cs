
private System.Windows.Forms.TextBox txtOrigin;
private System.Windows.Forms.TextBox txtVia;
private System.Windows.Forms.TextBox txtDestination;
private System.Windows.Forms.Button btnCalculate;
private System.Windows.Forms.Label lblResult;

namespace RailRouteGUI;

partial class Form1
{
    /// <summary>
    ///  Required designer variable.
    /// </summary>
    private System.ComponentModel.IContainer components = null;

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

    /// <summary>
    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    /// </summary>
    private void InitializeComponent()
    {
        // Origin
        this.txtOrigin = new System.Windows.Forms.TextBox();
        this.txtOrigin.Location = new System.Drawing.Point(20, 20);
        this.txtOrigin.Size = new System.Drawing.Size(200, 22);
        this.txtOrigin.PlaceholderText = "Origin City";
        this.Controls.Add(this.txtOrigin);

        // Via
        this.txtVia = new System.Windows.Forms.TextBox();
        this.txtVia.Location = new System.Drawing.Point(20, 60);
        this.txtVia.Size = new System.Drawing.Size(200, 22);
        this.txtVia.PlaceholderText = "Via (comma-separated)";
        this.Controls.Add(this.txtVia);

        // Destination
        this.txtDestination = new System.Windows.Forms.TextBox();
        this.txtDestination.Location = new System.Drawing.Point(20, 100);
        this.txtDestination.Size = new System.Drawing.Size(200, 22);
        this.txtDestination.PlaceholderText = "Destination City";
        this.Controls.Add(this.txtDestination);

        // Button
        this.btnCalculate = new System.Windows.Forms.Button();
        this.btnCalculate.Location = new System.Drawing.Point(20, 140);
        this.btnCalculate.Size = new System.Drawing.Size(200, 30);
        this.btnCalculate.Text = "Calculate Route";
        this.btnCalculate.Click += new System.EventHandler(this.btnCalculate_Click);
        this.Controls.Add(this.btnCalculate);

        // Result Label
        this.lblResult = new System.Windows.Forms.Label();
        this.lblResult.Location = new System.Drawing.Point(20, 190);
        this.lblResult.Size = new System.Drawing.Size(600, 400);
        this.lblResult.AutoSize = false;
        this.lblResult.Text = "Route summary will appear here";
        this.lblResult.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
        this.lblResult.BackColor = System.Drawing.Color.White;
        this.lblResult.Padding = new Padding(5);
        this.Controls.Add(this.lblResult);
        components = new System.ComponentModel.Container();
        AutoScaleMode = AutoScaleMode.Font;
        ClientSize = new Size(800, 450);
        Text = "Form1";
    }

    #endregion
}
