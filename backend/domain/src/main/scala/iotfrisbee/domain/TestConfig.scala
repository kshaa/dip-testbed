package iotfrisbee.domain

case class TestConfig(testName: Option[String])
object TestConfig {
  def fromConfig(enabled: Option[Boolean], testName: Option[String]): TestConfig = {
    if (enabled.getOrElse(false)) {
      TestConfig(testName)
    } else {
      TestConfig(None)
    }
  }
}
