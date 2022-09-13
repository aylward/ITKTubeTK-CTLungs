import os
import sys
import subprocess

import math

from pathlib import Path

import csv

import numpy as np

import itk
from itk import TubeTK as tube


def ctl_is_bundled():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


#################
#################
#################
#################
#################
class CTLungs:
    def __init__(self, ct_image):
        self.ImageTypeF = itk.Image[itk.F, 3]
        self.ImageTypeUC = itk.Image[itk.UC, 3]
        self.ImageTypeSS = itk.Image[itk.SS, 3]

        self.ct_image = ct_image
        self.ct_iso = 0
        self.lungs_mask = 0
        self.ct_lungs = 0

        self.spacing = ct_image.GetSpacing()[1]

        self.report_progress = print
        self.debug = False
        self.debug_output_dir = "./"

        self.ct_min = -1024
        self.ct_max = 4096

        self.ct_air_max = -900
        self.ct_lungs_max = -500

        self.ct_vessels_min = -100
        self.ct_vessels_max = 2048

        self.num_sample_seeds = 15
        self.sample_vessels_mask = 0

        self.ct_lungs_vessels_enhanced = 0
        self.ct_lungs_vessels_enhanced_core = 0

        self.ct_lungs_vessels_input = 0

        self.lungs_vessels_seeds = 0
        self.lungs_vessels_radius = 0
        self.lungs_vessels_start_specificity = 0.95
        self.lungs_vessels_end_specificity = 0.95

        self.num_vessels = 2000

        self.lungs_vessels = 0
        self.lungs_vessels_mask = 0

    def make_isotropic(self):
        self.report_progress("Make Isotropic", 50)
        resamp = tube.ResampleImage[self.ImageTypeF].New(Input=self.ct_image)
        resamp.SetMakeIsotropic(True)
        resamp.Update()
        self.ct_iso = resamp.GetOutput()

    def segment_lungs(self):
        ImageMath = tube.ImageMath.New(self.ct_iso)

        # Segment air
        self.report_progress("Segment Air", 0)
        ImageMath.ConnectedComponents(self.ct_min, self.ct_air_max, 1, 0, 0, 0)
        ImageMath.Dilate(10, 1, 0)
        ImageMath.Erode(20, 1, 0)
        self.report_progress("Segment Air", 10)
        ImageMath.Dilate(11, 1, 0)
        imBkgMask = ImageMath.GetOutput()

        # Segment lung
        self.report_progress("Segment Lung", 20)
        ImageMath.SetInput(self.ct_iso)
        ImageMath.ReplaceValuesOutsideMaskRange(imBkgMask, 0, 0, self.ct_min)
        ImageMath.Threshold(self.ct_min + 1, self.ct_lungs_max, 1, 0)
        ImageMath.Dilate(5, 1, 0)
        ImageMath.Erode(10, 1, 0)
        self.report_progress("Segment Lung", 30)
        ImageMath.Dilate(3, 1, 0)
        imLungsPlusMask = ImageMath.GetOutputUChar()

        self.report_progress("Connected Components", 50)
        ConnComp = tube.SegmentConnectedComponents.New(imLungsPlusMask)
        ConnComp.SetMinimumVolume(10000)
        ConnComp.Update()
        self.lungs_mask = ConnComp.GetOutput()
        self.report_progress("Connected Components", 70)
        castImageFilter = itk.CastImageFilter[self.ImageTypeUC, self.ImageTypeF].New()
        castImageFilter.SetInput(self.lungs_mask)
        castImageFilter.Update()
        tmp_img = castImageFilter.GetOutput()

        self.report_progress("Generate Mask", 90)
        ImageMath.SetInput(self.ct_iso)
        ImageMath.ReplaceValuesOutsideMaskRange(tmp_img, 1, 9999, self.ct_min - 1)
        self.ct_lungs = ImageMath.GetOutput()

    def extract_sample_vessels(self):
        self.report_progress("Extract Sample Vessels", 0)

        self.report_progress("Create lung core mask", 10)
        # Erode imLungs to avoid noise at edges
        imMath = tube.ImageMath.New(self.ct_lungs)
        imMath.Threshold(self.ct_min - 1, self.ct_min - 1, 0, 1)
        imMath.Erode(10, 1, 0)
        imLungsMaskErode = imMath.GetOutput()

        self.report_progress("Create lung core mask", 20)
        imMath.SetInput(self.ct_lungs)
        imMath.IntensityWindow(self.ct_vessels_min, self.ct_vessels_max, 0, 1)
        imMath.ReplaceValuesOutsideMaskRange(imLungsMaskErode, 0.5, 1.5, 0)
        imLungsErode = imMath.GetOutput()

        self.report_progress("Create lung core mask", 30)
        imMath.SetInput(imLungsErode)
        imMath.Blur(4 * self.spacing)
        imBlurBig = imMath.GetOutput()

        self.report_progress("Create lung vessel mask", 40)
        imMath.SetInput(self.ct_lungs)
        imMath.Blur(0.5 * self.spacing)
        imMath.AddImages(imBlurBig, 1, -1)
        imDoG = imMath.GetOutput()

        imDoGArray = itk.GetArrayFromImage(imDoG)

        seedCoverage = 20
        seedCoord = np.zeros([self.num_sample_seeds, 3])
        self.report_progress("Finding seeds", 50)
        for i in range(self.num_sample_seeds):
            seedCoord[i] = np.unravel_index(
                np.argmax(imDoGArray, axis=None), imDoGArray.shape
            )
            indx = [int(seedCoord[i][0]), int(seedCoord[i][1]), int(seedCoord[i][2])]
            minX = max(indx[0] - seedCoverage, 0)
            maxX = min(indx[0] + seedCoverage, imDoGArray.shape[0])
            minY = max(indx[1] - seedCoverage, 0)
            maxY = min(indx[1] + seedCoverage, imDoGArray.shape[1])
            minZ = max(indx[2] - seedCoverage, 0)
            maxZ = min(indx[2] + seedCoverage, imDoGArray.shape[2])
            imDoGArray[minX:maxX, minY:maxY, minZ:maxZ] = -1024
            indx.reverse()
            seedCoord[:][i] = self.ct_lungs.TransformIndexToPhysicalPoint(indx)
        print(seedCoord)

        self.report_progress("Extracting vessels at seeds", 70)
        # Manually extract a few vessels to form an image-specific training set
        vSeg = tube.SegmentTubes.New(Input=self.ct_lungs)
        vSeg.SetVerbose(True)
        vSeg.SetMinRoundness(0.4)
        vSeg.SetMinRidgeness(0.8)
        # vSeg.SetMinCurvature(0.02)
        vSeg.SetRadiusInObjectSpace(self.spacing)
        vSeg.SetMinLength(300)
        for i in range(self.num_sample_seeds):
            print("**** Processing seed " + str(i) + " : " + str(seedCoord[i]))
            self.report_progress(
                "Extracting vessels at seeds", 70 + i * (30 / self.num_sample_seeds)
            )
            vSeg.ExtractTubeInObjectSpace(seedCoord[i], i)

        self.sample_vessels_mask = vSeg.GetTubeMaskImage()

    def enhance_vessels(self):
        self.report_progress("Enhancing Vessels", 0)

        self.report_progress("Generate training mask", 10)
        trMask = tube.ComputeTrainingMask[self.ImageTypeF, self.ImageTypeUC].New()
        trMask.SetInput(self.sample_vessels_mask)
        trMask.SetGap(3)
        trMask.SetObjectWidth(1)
        trMask.SetNotObjectWidth(1)
        trMask.Update()
        fgMask = trMask.GetOutput()

        imMath = tube.ImageMath.New(fgMask)
        imMath.ReplaceValuesOutsideMaskRange(self.lungs_mask, 1, 99999, 64)
        fgMask = imMath.GetOutput()

        if self.debug:
            itk.imwrite(
                fgMask, os.path.join(self.debug_output_dir, "vessels_training_mask.mha")
            )

        self.report_progress("Modeling", 40)
        enhancer = tube.EnhanceTubesUsingDiscriminantAnalysis[
            self.ImageTypeF, self.ImageTypeUC
        ].New()
        enhancer.AddInput(self.ct_lungs)
        enhancer.SetLabelMap(fgMask)
        enhancer.SetRidgeId(255)
        enhancer.SetBackgroundId(128)
        enhancer.SetUnknownId(0)
        enhancer.SetIgnoreId(64)
        enhancer.SetTrainClassifier(True)
        enhancer.SetUseIntensityOnly(True)
        enhancer.SetUseFeatureMath(True)
        enhancer.SetScales([1 * self.spacing, 2 * self.spacing, 6 * self.spacing])
        # Previously (size*0.5,size*1.5,size*3.5,size*5.5)
        enhancer.Update()
        self.report_progress("Classifying", 50)
        enhancer.ClassifyImages()

        if self.debug:
            itk.imwrite(
                enhancer.GetClassProbabilityImage(0),
                os.path.join(self.debug_output_dir, "vessels_prob_0.mha"),
            )
            itk.imwrite(
                enhancer.GetClassProbabilityImage(1),
                os.path.join(self.debug_output_dir, "vessels_prob_1.mha"),
            )

        self.report_progress("Likelihood", 60)
        imMath = tube.ImageMath.New(enhancer.GetClassProbabilityImage(0))
        imMath.Blur(0.5 * self.spacing)
        prob0 = imMath.GetOutput()
        imMath.SetInput(enhancer.GetClassProbabilityImage(1))
        imMath.Blur(0.5 * self.spacing)
        prob1 = imMath.GetOutput()

        imMath.SetInput(self.ct_lungs)
        imMath.Threshold(-1025, -1025, 0, 1)
        imMath.Erode(2, 1, 0)
        imLungsE = imMath.GetOutput()

        self.report_progress("Likelihood class 0", 70)
        imMath.SetInput(prob0)
        imMath.ReplaceValuesOutsideMaskRange(imLungsE, 1, 1, 0)
        prob0 = imMath.GetOutput()

        self.report_progress("Likelihood class 0", 80)
        imMath.SetInput(prob1)
        imMath.ReplaceValuesOutsideMaskRange(imLungsE, 1, 1, 0)
        prob1 = imMath.GetOutput()

        self.report_progress("Likelihood ensemble", 90)
        imDiff = itk.SubtractImageFilter(Input1=prob0, Input2=prob1)
        imDiffArr = itk.GetArrayFromImage(imDiff)
        dMax = imDiffArr.max()
        imProbArr = imDiffArr / dMax
        imLungsVess = itk.GetImageFromArray(imProbArr)
        imLungsVess.CopyInformation(self.ct_lungs)

        imMath.SetInput(imLungsVess)
        imMath.ReplaceValuesOutsideMaskRange(imLungsE, 1, 1, -1)
        self.ct_lungs_vessels_enhanced = imMath.GetOutput()

        imMath.SetInput(self.ct_lungs)
        imMath.Threshold(self.ct_min - 1, self.ct_min - 1, 0, 1)
        imMath.Erode(8, 1, 0)
        imMaskedE = imMath.GetOutput()

        imMath.SetInput(self.ct_lungs_vessels_enhanced)
        imMath.ReplaceValuesOutsideMaskRange(imMaskedE, 1, 1, -1)
        self.ct_lungs_vessels_enhanced_core = imMath.GetOutput()

    def extract_vessels(self):
        self.report_progress("Generate seeds", 10)
        imMath = tube.ImageMath.New(self.ct_lungs_vessels_enhanced)
        imMath.MedianFilter(1)
        imMath.Threshold(0.000001, 1, 1, 0)
        im1VessMask = imMath.GetOutputShort()

        self.report_progress("Filter seeds", 20)
        ccSeg = tube.SegmentConnectedComponents.New(im1VessMask)
        ccSeg.SetMinimumVolume(100)
        ccSeg.Update()
        tmp_img = ccSeg.GetOutput()
        castImageFilter = itk.CastImageFilter[self.ImageTypeSS, self.ImageTypeF].New()
        castImageFilter.SetInput(tmp_img)
        castImageFilter.Update()
        self.lungs_vessels_initial_mask = castImageFilter.GetOutput()

        if self.debug:
            itk.imwrite(
                self.lungs_vessels_initial_mask,
                os.path.join(self.debug_output_dir, "vessels_initial_mask.mha"),
            )

        self.report_progress("Generate seed mask", 25)
        imMath.SetInput(self.ct_lungs_vessels_enhanced_core)
        imMath.ReplaceValuesOutsideMaskRange(
            self.lungs_vessels_initial_mask, 1, 99999, 0
        )
        self.lungs_vessels_seeds = imMath.GetOutput()

        if self.debug:
            itk.imwrite(
                self.lungs_vessels_seeds,
                os.path.join(self.debug_output_dir, "vessels_seeds.mha"),
            )

        imMath.SetInput(self.lungs_vessels_initial_mask)
        imMath.Threshold(0, 0, 1, 0)
        im1VessMaskInv = imMath.GetOutput()

        self.report_progress("Generate radius estimates", 30)
        distFilter = itk.DanielssonDistanceMapImageFilter.New(im1VessMaskInv)
        distFilter.Update()
        dist = distFilter.GetOutput()

        imMath.SetInput(dist)
        imMath.Blur(0.4)
        tmp = imMath.GetOutput()
        imMath.ReplaceValuesOutsideMaskRange(tmp, 0.1, 10, 0)
        self.lungs_vessels_radius = imMath.GetOutput()

        if self.debug:
            itk.imwrite(
                self.lungs_vessels_radius,
                os.path.join(self.debug_output_dir, "vessels_radius.mha"),
            )

        self.report_progress("Generate input image", 40)
        imMath.SetInput(self.ct_lungs_vessels_enhanced)
        # imMath.ReplaceValuesOutsideMaskRange(
        # self.ct_lungs_vessels_enhanced_core,
        # 1, 99999, 0)
        imMath.Blur(self.spacing / 2)
        self.ct_lungs_vessels_input = imMath.GetOutput()

        if self.debug:
            itk.imwrite(
                self.ct_lungs_vessels_input,
                os.path.join(self.debug_output_dir, "vessels_input.mha"),
            )

        seed_min_prob = 0.75 * self.lungs_vessels_start_specificity
        vessel_min_curvature = 0.0175 * self.lungs_vessels_end_specificity**2
        vessel_min_roundness = 0.2 + 0.2 * self.lungs_vessels_end_specificity
        vessel_min_ridgeness = 0.6 + 0.4 * math.sqrt(self.lungs_vessels_end_specificity)
        vessel_min_length = 200

        self.report_progress("Extract vessels", 45)
        vSeg = tube.SegmentTubes.New(Input=self.ct_lungs_vessels_input)
        # vSeg.SetVerbose(True)
        vSeg.SetMinCurvature(vessel_min_curvature)
        vSeg.SetMinRoundness(vessel_min_roundness)
        vSeg.SetMinRidgeness(vessel_min_ridgeness)
        vSeg.SetMinLevelness(0.0)
        vSeg.SetMinLength(vessel_min_length)
        vSeg.SetRadiusInObjectSpace(1.5 * self.spacing)
        vSeg.SetBorderInIndexSpace(3)
        vSeg.SetSeedMask(self.lungs_vessels_seeds)
        vSeg.SetSeedRadiusMask(self.lungs_vessels_radius)
        vSeg.SetOptimizeRadius(True)
        vSeg.SetSeedMaskMaximumNumberOfPoints(self.num_vessels)
        vSeg.SetUseSeedMaskAsProbabilities(True)
        vSeg.SetSeedExtractionMinimumProbability(seed_min_prob)
        vSeg.ProcessSeeds()

        self.lungs_vessels_mask = vSeg.GetTubeMaskImage()

        self.lungs_vessels = vSeg.GetTubeGroup()

    def post_process_vessels(self):
        self.report_progress("Smoothing vessels", 50)
        TubeMath = tube.TubeMath[3, itk.F].New()
        TubeMath.SetInputTubeGroup(self.lungs_vessels)
        TubeMath.SetUseAllTubes()
        TubeMath.SmoothTube(4, "SMOOTH_TUBE_USING_INDEX_GAUSSIAN")
        self.lungs_vessels = TubeMath.GetOutputTubeGroup()
