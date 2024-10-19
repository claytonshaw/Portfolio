load('cirrhosis.Rdata')
source('kappa and classsum.R')
library(EZtune)
library(randomForest)
library(rpart)
library(caret)
set.seed(69)

# adding a binary response variable
cirrhosis_train_binary = cirrhosis_train
cirrhosis_test_binary = cirrhosis_test
cirrhosis_train_binary$Status = as.integer(cirrhosis_train_binary$Status == 'D')
cirrhosis_test_binary$Status = as.integer(cirrhosis_test_binary$Status == 'D')

##############################################################################
## LOGISTIC REGRESSION
##############################################################################

# Logistic Regression
cirrhosis_lr = glm(Status ~ ., family = binomial, 
                   data = cirrhosis_train_binary)

# 10 fold cross validation without variable selection
status_lr_xval <- rep(0, nrow(cirrhosis_train_binary))
xvs <- rep(1:10, length = nrow(cirrhosis_train_binary))
xvs <- sample(xvs)
for (i in 1:10) {
  train <- cirrhosis_train_binary[xvs != i, ]
  test <- cirrhosis_train_binary[xvs == i, ]
  glub <- glm(Status ~ ., family = binomial, data = train)
  status_lr_xval[xvs == i] <- predict(glub, test, type = "response")
}
table(cirrhosis_train_binary$Status, round(status_lr_xval))
class.sum(cirrhosis_train_binary$Status, status_lr_xval)
"Accuracy: 78.26%"

# Feature Selection
stepwise_model = step(cirrhosis_lr, direction = 'backward')

# 10 fold cross validation with feature selection
status_lr14_xval <- rep(0, nrow(cirrhosis_train_binary))
xvs <- rep(1:10, length = nrow(cirrhosis_train_binary))
xvs <- sample(xvs)
for (i in 1:10) {
  train <- cirrhosis_train_binary[xvs != i, ]
  test <- cirrhosis_train_binary[xvs == i, ]
  glub <- step(glm(Status ~ ., family = binomial, data = train))
  status_lr14_xval[xvs == i] <- predict(glub, test, type = "response")
}
table(cirrhosis_train_binary$Status, round(status_lr14_xval))
class.sum(cirrhosis_train_binary$Status, status_lr14_xval)
"Accuracy: 79.71"

# Predicting onto test data
status_lr14_test = predict(stepwise_model, cirrhosis_test_binary, type = "response")
table(cirrhosis_test_binary$Status, round(status_lr14_test))
class.sum(cirrhosis_test_binary$Status, status_lr14_test)
"Accuracy: 79.05"

"Add what variables I ended up keeping!!!!"

##############################################################################
## KNN
##############################################################################

# setting up cross validation
control = trainControl(method = "cv", number = 10)
grid = expand.grid(k = 1:20)

# knn model
knn_model = train(Status ~ ., data = cirrhosis_train, method = "knn",
                   trControl = control, tuneGrid = grid)

print(knn_model)
"Best Model was k=13"
'Accuracy was 71.95%'

# predicting onto test data
knn_predictions = predict(knn_model, newdata = cirrhosis_test)
confusionMatrix(knn_predictions, cirrhosis_test$Status)
"Accuracy: 67.62%"

##############################################################################
## Decision Tree
##############################################################################

full_tree = rpart(Status ~ ., data = cirrhosis_train,
                       control = rpart.control(cp = 0.0, minsplit = 2))

plotcp(full_tree)
'cp=0.025, 0.019, 0.036' 

cp_value = c(0.025, 0.019, 0.036)


pruned_tree_model = train(Status ~ ., data = cirrhosis_train, method = "rpart", 
                           trControl = control, 
                          tuneGrid = data.frame(cp = cp_value))
print(pruned_tree_model)
'Accuracy: 65.67%'

pruned_tree = prune(full_tree, cp = 0.036)

plot(pruned_tree, margin = 0.1)
text(pruned_tree)

# predicting onto test data
tree_predictions = predict(pruned_tree, newdata = cirrhosis_test, 
                      type = "class")
confusionMatrix(tree_predictions, cirrhosis_test$Status)
'Accuracy: 72.38%'

##############################################################################
## Random Forests
##############################################################################

cirrhosis_forest = randomForest(Status ~., 
                                data = cirrhosis_train, 
                                ntree=1000
                                )
print(cirrhosis_forest)
"Out of Bag Accuracy: 73.43"

# variable importance
varImpPlot(cirrhosis_forest, scale=FALSE)
cirrhosis_forest2 = randomForest(Status ~ N_Days + Bilirubin + Copper +
                                   Prothrombin + Alk_Phos,
                                 data = cirrhosis_train, 
                                 ntree=1000)

print(cirrhosis_forest2)
"Accuracy: 74.4%"

# predicting onto test data
rf_predictions = predict(cirrhosis_forest2, newdata = cirrhosis_test, 
                         type='class')
confusionMatrix(rf_predictions, cirrhosis_test$Status)
'Accuracy: 76.19%'

##############################################################################
## Adaboost
##############################################################################

# tuning the adaboost model
tuned_ada = eztune(x = subset(cirrhosis_train_binary, select = -Status),
                   y = cirrhosis_train_binary$Status,
                   method = 'ada',
                   fast = TRUE
                   )
results_ada = eztune_cv(x = subset(cirrhosis_train_binary, select = -Status),
          y = cirrhosis_train_binary$Status,
          tuned_ada,
          cross=10)

tuned_ada
"Accuracy 100% Something wrong"
# predicting on to the test data
ada_pred = predict(tuned_ada, newdata = cirrhosis_test_binary)
mean(ada_pred$predictions == cirrhosis_test_binary$Status)
"Accuracy: 79.05%" 


##############################################################################
## Gradient Boosting Machine
##############################################################################

# tuning GBM

tuned_gbm = eztune(x = subset(cirrhosis_train_binary, select = -Status), 
                        y = cirrhosis_train_binary$Status, 
                        method='gbm', fast = TRUE)
eztune_cv(x = subset(cirrhosis_train_binary, select = -Status),
          y = cirrhosis_train_binary$Status,
          tuned_gbm,
          cross = 10)
'Accuracy: 78.74%'

tuned_gbm

# predicting onto newvalid data with tuning
gbm_pred = predict(tuned_gbm, newdata = cirrhosis_test_binary)
mean(gbm_pred$predictions == cirrhosis_test_binary$Status)
"Accuracy: 82.85%"

##############################################################################
## Support Vector Machine
##############################################################################

tuned_svm = eztune(x = subset(cirrhosis_train_binary, select = -Status),
                   y = cirrhosis_train_binary$Status,
                   method = 'svm',
                   fast = TRUE)

eztune_cv(x = subset(cirrhosis_train_binary, select = -Status),
          y = cirrhosis_train_binary$Status,
          tuned_svm,
          cross = 10)
tuned_svm
'Accuracy: 71.01%'

# predicting onto the test data
svm_pred = predict(tuned_svm, newdata = cirrhosis_test_binary)
mean(svm_pred$predictions == cirrhosis_test_binary$Status)
'Accurcy: 75.23%'

