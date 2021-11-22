package com.example.nextar;

import android.content.Context;
import com.google.ar.core.Anchor;
import com.google.ar.core.AugmentedImage;
import com.google.ar.core.Pose;
import rendering.ObjectRenderer;
import rendering.ObjectRenderer.BlendMode;
import java.io.IOException;

/** Renders an augmented image. */
public class AugmentedImageRenderer {
    private static final String TAG = "AugmentedImageRenderer";

    private static final float TINT_INTENSITY = 0.1f;
    private static final float TINT_ALPHA = 1.0f;
    private static final int[] TINT_COLORS_HEX = {
            0x000000, 0xF44336, 0xE91E63, 0x9C27B0, 0x673AB7, 0x3F51B5, 0x2196F3, 0x03A9F4, 0x00BCD4,
            0x009688, 0x4CAF50, 0x8BC34A, 0xCDDC39, 0xFFEB3B, 0xFFC107, 0xFF9800,
    };

    private final ObjectRenderer allDefectsRenderer = new ObjectRenderer();

    public AugmentedImageRenderer() {}

    public void createOnGlThread(Context context) throws IOException {
        //this is where the model should be passed into the code from a selection from the user's files
        allDefectsRenderer.createOnGlThread(
                context, "models/originalCadNoScale.obj", "models/yellow.png");
        allDefectsRenderer.setMaterialProperties(0.3f, 1.0f, 1.0f, 6.0f);
        //going to have to figure out a way to set the #diffuseTextureAssetName to different pngs based on the material file of the obj
    }

    public void draw(
            float[] viewMatrix,
            float[] projectionMatrix,
            AugmentedImage augmentedImage,
            Anchor centerAnchor,
            float[] colorCorrectionRgba) {
        float[] tintColor =
                convertHexToColor(TINT_COLORS_HEX[augmentedImage.getIndex() % TINT_COLORS_HEX.length]);

        //final float mazeEdgeSize = 492.65f; // Magic number of maze size
        final float mazeEdgeSize = 100.65f; //just a test. going down in edge size makes the image larger
        final float maxImageEdgeSize = Math.max(augmentedImage.getExtentX(), augmentedImage.getExtentZ()); // Get largest detected image edge size

        Pose anchorPose = centerAnchor.getPose();

        float mazeScaleFactor = maxImageEdgeSize / mazeEdgeSize; // scale to set Maze to image size
        float[] modelMatrix = new float[16];

        // OpenGL Matrix operation is in the order: Scale, rotation and Translation
        // So the manual adjustment is after scale
        // The 251.3f and 129.0f is magic number from the maze obj file
        // You mustWe need to do this adjustment because the maze obj file
        // is not centered around origin. Normally when you
        // work with your own model, you don't have this problem.
        Pose mazeModelLocalOffset = Pose.makeTranslation(
                -251.3f * mazeScaleFactor,
                0.0f,
                29.0f * mazeScaleFactor);
        anchorPose.compose(mazeModelLocalOffset).toMatrix(modelMatrix, 0);
        allDefectsRenderer.updateModelMatrix(modelMatrix, mazeScaleFactor, mazeScaleFactor/10.0f, mazeScaleFactor); // This line relies on a change in ObjectRenderer.updateModelMatrix later in this codelab.
        allDefectsRenderer.draw(viewMatrix, projectionMatrix, colorCorrectionRgba, tintColor);
    }

    private static float[] convertHexToColor(int colorHex) {
        // colorHex is in 0xRRGGBB format
        float red = ((colorHex & 0xFF0000) >> 16) / 255.0f * TINT_INTENSITY;
        float green = ((colorHex & 0x00FF00) >> 8) / 255.0f * TINT_INTENSITY;
        float blue = (colorHex & 0x0000FF) / 255.0f * TINT_INTENSITY;
        return new float[] {red, green, blue, TINT_ALPHA};
    }
}

