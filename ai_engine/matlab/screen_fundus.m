function [predictedClass, drLevel, confidencePercent, referable, lowConfidence, gradCAMFile] = screen_fundus(modelFile, imageFile, gradCAMFile)
% Run the supplied trainedDRModel.mat net and generate Grad-CAM output.

persistent net loadedModelFile;
if isempty(net) || isempty(loadedModelFile) || ~strcmp(loadedModelFile, modelFile)
    loaded = load(modelFile, 'net');
    net = loaded.net;
    loadedModelFile = modelFile;
end
patientImage = imread(imageFile);
inputSize = net.Layers(1).InputSize;

patientInput = imresize(patientImage, inputSize(1:2));
patientInput = im2single(patientInput);
patientInput = dlarray(patientInput, 'SSC');
scores = predict(net, patientInput);
probabilities = softmax(extractdata(scores));
[confidence, idx] = max(probabilities);

classNames = ["No_DR", "Mild", "Moderate", "Severe", "Proliferate_DR"];
predictedClass = classNames(idx);
drLevel = idx - 1;
confidencePercent = confidence * 100;
referable = drLevel >= 2;
lowConfidence = confidencePercent < 50;

if ~isempty(gradCAMFile)
    gradImage = im2single(imresize(patientImage, inputSize(1:2)));
    scoreMap = gradCAM(net, gradImage, idx, FeatureLayer="res5b_relu", ReductionLayer="prob");
    outputFolder = fileparts(gradCAMFile);
    if ~isempty(outputFolder) && ~isfolder(outputFolder)
        mkdir(outputFolder);
    end
    figureHandle = figure('Visible', 'off');
    imshow(gradImage);
    hold on;
    imagesc(rescale(scoreMap), 'AlphaData', 0.5);
    axis image off;
    colormap jet;
    exportgraphics(gca, gradCAMFile);
    close(figureHandle);
end
end
