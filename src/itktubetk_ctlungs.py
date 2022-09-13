import os
import sys
import subprocess
import pathlib
from pathlib import Path
import csv
import numpy as np

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
from tkinter.ttk import Progressbar

import webbrowser

import itk
from itk import TubeTK as tube


def is_bundled():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_lib_path():
    if is_bundled():
        return os.path.join(sys._MEIPASS, "itktubetk_ctlungs")
    return os.path.dirname(os.path.realpath(__file__)) + "/../lib"


def get_bin_path():
    if is_bundled():
        return os.path.join(sys._MEIPASS, "itktubetk_ctlungs", "bin")
    return os.path.dirname(os.path.realpath(__file__)) + "/bin"


sys.path.append(get_lib_path())
from itktubetk_ctlungs_lib import *
from ToggledFrame import *


class CTLungs_App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.ctl = 0

        self.ct_file = "../data/CT/CT.mha"

        self.dcm_in_dir = "./"
        self.dcm_out_dir = "./"

        self.process_out_dir = "../data/results"

        self.vessels_start_specificity = tk.DoubleVar()
        self.vessels_end_specificity = tk.DoubleVar()

        self.progress_status = ""

        self.reprocess = False

        self.title("ITKTubeTK CT Lungs")

        frm_title = tk.Frame(master=self)
        lbl_title = tk.Label(
            master=frm_title, text="ITKTubeTK CT Lungs", font=("Helvetica", 16, "bold")
        ).pack(pady=5)
        self.debug = tk.IntVar()
        ckb_debug = tk.Checkbutton(
            master=frm_title,
            text="Debug",
            variable=self.debug,
            pady=5,
            command=self.hdl_debug,
        ).pack()
        frm_title.pack(fill=tk.BOTH)

        ###
        ### Utility Functions
        ###

        frm_utility = tk.Frame(
            master=self, relief=tk.RIDGE, borderwidth=5, bg="light yellow", pady=5
        )
        lbl_utility = tk.Label(
            master=frm_utility, text="Utility Functions", bg="light yellow"
        ).pack()
        btn_dcm = tk.Button(
            master=frm_utility,
            text="Convert DICOM files",
            command=self.hdl_dcm,
            width=20,
        ).pack(pady=5)
        btn_view = tk.Button(
            master=frm_utility, text="View a file", command=self.hdl_view, width=20
        ).pack(pady=5)
        btn_help = tk.Button(
            master=frm_utility, text="Help", command=self.hdl_help, width=20
        ).pack(pady=5)
        frm_utility.pack(fill=tk.X)

        ###
        ### Process
        ###

        frm_process = tk.Frame(
            master=self, relief=tk.RIDGE, borderwidth=5, bg="light green", pady=5
        )

        lbl_process = tk.Label(
            master=frm_process, text="Process Lung CT file", bg="light green"
        ).pack()

        btn_ct_file = tk.Button(
            master=frm_process, text="Load CT file", command=self.hdl_ct_file, width=20
        ).pack(pady=5)

        btn_out_dir = tk.Button(
            master=frm_process,
            text="Set Output Directory",
            command=self.hdl_process_out_dir,
            width=20,
        ).pack(pady=5)

        sld_start_specificity = tk.Scale(
            master=frm_process,
            label="Vessel Starting Specificity",
            from_=0.0,
            to=100.0,
            orient=tk.HORIZONTAL,
            var=self.vessels_start_specificity,
            bg="light green",
            length=140,
        ).pack(padx=5, pady=5)
        self.vessels_start_specificity.set(50)

        sld_end_specificity = tk.Scale(
            master=frm_process,
            label="Vessel Ending Specificity",
            from_=0.0,
            to=100.0,
            orient=tk.HORIZONTAL,
            var=self.vessels_end_specificity,
            bg="light green",
            length=140,
        ).pack(padx=5, pady=5)
        self.vessels_end_specificity.set(50)

        self.btn_process = tk.Button(
            master=frm_process,
            text="Process",
            command=self.hdl_process,
            width=20,
        ).pack(pady=5)

        frm_process.pack(padx=5, fill=tk.BOTH)

        ###
        ### ADVANCED OPTIONS
        ###

        frm_adv = ToggledFrame(
            master=self,
            relief=tk.RIDGE,
            text="Advanced Options",
            borderwidth=5,
            bg="light sky blue",
            pady=5,
        )
        frm_adv.pack(fill=tk.X)

        btn_prep_ct = tk.Button(
            master=frm_adv.sub_frame,
            text="Make CT Isotropic",
            command=self.hdl_prep_ct,
            width=20,
        ).pack(pady=5)

        btn_seg_lungs = tk.Button(
            master=frm_adv.sub_frame,
            text="Segment Lungs",
            command=self.hdl_seg_lungs,
            width=20,
        ).pack(pady=5)

        btn_enh_vess = tk.Button(
            master=frm_adv.sub_frame,
            text="Enhance Vessels",
            command=self.hdl_enh_vess,
            width=20,
        ).pack(pady=5)

        btn_ext_vess = tk.Button(
            master=frm_adv.sub_frame,
            text="Extract Vessels",
            command=self.hdl_ext_vess,
            width=20,
        ).pack(pady=5)

        btn_post_vess = tk.Button(
            master=frm_adv.sub_frame,
            text="Post Process Vessels",
            command=self.hdl_post_vess,
            width=20,
        ).pack(pady=5)

        frm_adv.pack(padx=5, fill=tk.BOTH)

        ###
        ### Progress
        ###

        frm_progress = tk.Frame(
            master=self, relief=tk.RIDGE, borderwidth=5, bg="light blue", pady=5
        )
        lbl_progress = tk.Label(
            master=frm_progress, text="Progress", bg="light blue"
        ).pack()

        self.lbl_progress = tk.Label(
            frm_progress, text="Status: Idle", bg="light blue", width=40
        )
        self.lbl_progress.pack()

        self.pgb_progress = Progressbar(
            frm_progress, orient=tk.HORIZONTAL, length=150, mode="determinate"
        )
        self.pgb_progress.pack()
        self.pgb_subprogress = Progressbar(
            frm_progress, orient=tk.HORIZONTAL, length=150, mode="determinate"
        )
        self.pgb_subprogress.pack()
        frm_progress.pack(fill=tk.BOTH)

    #################################
    #################################
    #################################
    def hdl_help(self):
        box_help = tk.messagebox.showinfo(
            title="Help",
            message="      Stoke Collateral Vessels \n"
            + "Kitware, Inc. and The University of North Carolina \n"
            + "\n"
            + "Use this program to generate vessel-augmented \n"
            + "perfusion research reports for patients with stroke. \n"
            + "\n"
            + 'This program is distributed "AS-IS" and is not \n'
            + "suitable for any expressed or implied purpose. In \n"
            + "particular, it should never be used for clinical \n"
            + "decision making. \n"
            + "\n"
            + "DICOM conversion provided by dcm2niix. \n"
            + "\n"
            + "Learn more at \n"
            + "   http://github.com/KitwareMedical/ \n"
            + "      ITKTubeTK-StrokeCollateralVessels",
        )

    #################################
    #################################
    #################################
    def hdl_dcm(self):
        win_dcm = tk.Tk()

        frm_title = tk.Frame(master=win_dcm)
        lbl_title = tk.Label(master=frm_title, text="DICOM Conversion", pady=5).pack(
            padx=5, pady=5
        )
        frm_title.pack(fill=tk.BOTH)

        btn_dcm_in_dir = tk.Button(
            master=win_dcm,
            text="1) Set input directory",
            command=self.hdl_dcm_in_dir,
            width=20,
        ).pack(padx=5, pady=5)
        btn_dcm_out_dir = tk.Button(
            master=win_dcm,
            text="2) Set output directory",
            command=self.hdl_dcm_out_dir,
            width=20,
        ).pack(padx=5, pady=5)
        btn_dcm_process = tk.Button(
            master=win_dcm,
            text="3) Process",
            command=self.hdl_dcm_process,
            bg="pale green",
            width=20,
        ).pack(padx=5, pady=5)

        win_dcm.mainloop()

    def hdl_dcm_in_dir(self):
        self.dcm_in_dir = os.path.realpath(
            tk.filedialog.askdirectory(
                title="Dicom input directory", initialdir=self.dcm_in_dir
            )
        )

    def hdl_dcm_out_dir(self):
        self.dcm_out_dir = os.path.realpath(
            tk.filedialog.askdirectory(
                title="Output directory", initialdir=self.dcm_out_dir
            )
        )

    def hdl_dcm_process(self):
        dcm2niix = os.path.realpath(os.path.join(get_bin_path(), "dcm2niix.exe"))
        self.report_progress("Converting", 50)
        self.report_subprogress("Using dcm2niix", 50)
        subprocess.call([dcm2niix, "-o", self.dcm_out_dir, self.dcm_in_dir])
        self.report_progress("Done", 100)

    #################################
    #################################
    #################################
    def hdl_debug(self):
        if self.ctl:
            self.ctl.debug = self.var.get()

    #################################
    #################################
    #################################
    def hdl_view(self):
        # view_file = os.path.realpath(tk.filedialog.askopenfilename())
        # uri = pathlib.Path(view_file).as_uri()
        # path,name = os.path.split(view_file)
        url = "https://kitware.github.io/paraview-glance/app/"
        # url += "?name=" + name
        # url += "&url=" + uri
        # print(url)
        webbrowser.open(url)

    #################################
    #################################
    #################################
    def report_progress(self, label, percentage):
        self.progress_status = label
        print(label)
        self.lbl_progress["text"] = label
        self.pgb_progress["value"] = percentage
        self.pgb_subprogress["value"] = 0
        self.update()

    def report_subprogress(self, label, percentage):
        progress_label = self.progress_status + ": " + label
        self.lbl_progress["text"] = progress_label
        print(progress_label)
        self.pgb_subprogress["value"] = percentage
        self.update()

    #################################
    #################################
    #################################
    def save_vessels(self, vess_so, base_filename):
        SOWriter = itk.SpatialObjectWriter[3].New()
        SOWriter.SetInput(vess_so)
        SOWriter.SetBinaryPoints(True)
        SOWriter.SetFileName(base_filename + ".tre")
        SOWriter.Update()

        VTPWriter = itk.WriteTubesAsPolyData.New()
        VTPWriter.SetInput(vess_so)
        VTPWriter.SetFileName(base_filename + ".vtp")
        VTPWriter.Update()

    #################################
    #################################
    #################################
    def hdl_ct_file(self):
        filepath, filename = os.path.split(self.ct_file)
        self.ct_file = tk.filedialog.askopenfilename(
            title="CT File", initialdir=filepath, initialfile=filename
        )
        self.report_progress("Reading image", 50)
        self.report_subprogress("Using ITK", 50)
        self.ct_image = itk.imread(self.ct_file)
        self.ctl = CTLungs(self.ct_image)
        self.ctl.debug = self.debug.get()
        self.ctl.report_progress = self.report_subprogress
        self.report_progress("Done", 100)
        self.reprocess = False

    def hdl_process_out_dir(self):
        self.process_out_dir = os.path.realpath(
            tk.filedialog.askdirectory(
                title="Output directory", initialdir=self.process_out_dir
            )
        )
        self.ctl.debug_output_dir = self.process_out_dir

    #################################
    #################################
    #################################
    def hdl_prep_ct(self):
        self.report_progress("Preparing CT", 0)
        self.ctl.make_isotropic()
        itk.imwrite(
            self.ctl.ct_iso,
            os.path.join(self.process_out_dir, "ct_iso.mha"),
            compression=True,
        )
        self.report_progress("Done!", 100)

    def hdl_seg_lungs(self):
        self.report_progress("Segment Lungs", 0)
        self.ctl.segment_lungs()
        itk.imwrite(
            self.ctl.ct_lungs,
            os.path.join(self.process_out_dir, "ct_lungs.mha"),
            compression=True,
        )
        self.report_progress("Done!", 100)

    def hdl_enh_vess(self):
        self.report_progress("Exatract Sample Vessels", 0)
        self.ctl.extract_sample_vessels()
        itk.imwrite(
            self.ctl.sample_vessels_mask,
            os.path.join(self.process_out_dir, "ct_sample_vessels_mask.mha"),
            compression=True,
        )
        self.report_progress("Enahnce Vessels", 50)
        self.ctl.enhance_vessels()
        itk.imwrite(
            self.ctl.ct_lungs_vessels_enhanced,
            os.path.join(self.process_out_dir, "ct_lungs_vessels_enhanced.mha"),
            compression=True,
        )
        self.report_progress("Done!", 100)

    def hdl_ext_vess(self):
        self.report_progress("Extract Vessels", 0)
        self.ctl.lungs_vessels_start_specificity = (
            self.vessels_start_specificity.get() / 100.0
        )
        self.ctl.lungs_vessels_end_specificity = (
            self.vessels_end_specificity.get() / 100.0
        )
        self.ctl.extract_vessels()
        itk.imwrite(
            self.ctl.lungs_vessels_mask,
            os.path.join(self.process_out_dir, "ct_lungs_vessels_mask.mha"),
            compression=True,
        )
        self.save_vessels(
            self.ctl.lungs_vessels,
            os.path.join(self.process_out_dir, "ct_lungs_vessels"),
        )
        self.report_progress("Done!", 100)

    def hdl_post_vess(self):
        self.report_progress("Post Process Vessels", 0)
        self.ctl.post_process_vessels()
        self.save_vessels(
            self.ctl.lungs_vessels,
            os.path.join(self.process_out_dir, "ct_lungs_vessels_post"),
        )
        self.report_progress("Done!", 100)

    #################################
    #################################
    #################################
    def hdl_process(self):
        if self.reprocess == False:
            self.reprocess = True
            self.report_progress("Preparing CT", 0)
            self.ctl.make_isotropic()
            itk.imwrite(
                self.ctl.ct_iso,
                os.path.join(self.process_out_dir, "ct_iso.mha"),
                compression=True,
            )
            self.report_progress("Segment Lungs", 10)
            self.ctl.segment_lungs()
            itk.imwrite(
                self.ctl.ct_lungs,
                os.path.join(self.process_out_dir, "ct_lungs.mha"),
                compression=True,
            )
            self.report_progress("Extract Sample Vessels", 20)
            self.ctl.extract_sample_vessels()
            itk.imwrite(
                self.ctl.sample_vessels_mask,
                os.path.join(self.process_out_dir, "ct_sample_vessels_mask.mha"),
                compression=True,
            )
            self.report_progress("Enahnce Vessels", 30)
            self.ctl.enhance_vessels()
            itk.imwrite(
                self.ctl.ct_lungs_vessels_enhanced,
                os.path.join(self.process_out_dir, "ct_lungs_vessels_enhanced.mha"),
                compression=True,
            )

        self.report_progress("Extract Vessels", 60)
        self.ctl.lungs_vessels_start_specificity = (
            self.vessels_start_specificity.get() / 100.0
        )
        self.ctl.lungs_vessels_end_specificity = (
            self.vessels_end_specificity.get() / 100.0
        )
        self.ctl.extract_vessels()
        itk.imwrite(
            self.ctl.lungs_vessels_mask,
            os.path.join(self.process_out_dir, "ct_lungs_vessels_mask.mha"),
            compression=True,
        )
        self.save_vessels(
            self.ctl.lungs_vessels,
            os.path.join(self.process_out_dir, "ct_lungs_vessels"),
        )
        self.report_progress("Post Process Vessels", 90)
        self.ctl.post_process_vessels()
        self.save_vessels(
            self.ctl.lungs_vessels,
            os.path.join(self.process_out_dir, "ct_lungs_vessels_post"),
        )

        self.report_progress("Done!", 100)


#################################
#################################
#################################
if __name__ == "__main__":
    app = CTLungs_App()
    app.mainloop()
