// Delivery after merge, and nightly. Not yet run: the Jenkins server is set up in issue #5.
pipeline {
  agent any
  options { disableConcurrentBuilds() }
  triggers {
    pollSCM('H/2 * * * *')
    cron('H 2 * * *')
  }
  environment { TAG = "${env.GIT_COMMIT.take(7)}" }
  stages {
    stage('Build') { steps { sh 'bash scripts/build_images.sh "$TAG"' } }
    // Replace with a registry push when the registry is chosen (issue #5)
    stage('Load') { steps { sh 'bash scripts/load_images.sh "$TAG"' } }
    stage('Deploy') { steps { sh 'bash scripts/deploy.sh "$TAG"' } }
    stage('Smoke') { steps { sh 'bash scripts/smoke_test.sh' } }
    stage('NetworkPolicy') { steps { sh 'bash scripts/netpol_test.sh' } }
    stage('Evaluation') {
      when {
        allOf {
          triggeredBy 'TimerTrigger'
          expression { fileExists('k8s/eval-job.yaml') }
        }
      }
      steps { sh 'kubectl apply -f k8s/eval-job.yaml && bash scripts/check_eval.sh' }
    }
  }
  post { failure { echo 'Pipeline failed, nothing promoted' } }
}
