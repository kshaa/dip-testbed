package iotfrisbee.domain

case class IotFrisbeeConfig(testConfig: TestConfig, clusterized: Boolean)
object IotFrisbeeConfig {
  def fromConfig(testConfig: TestConfig, clusterized: Option[Boolean]): IotFrisbeeConfig =
    IotFrisbeeConfig(testConfig, clusterized.getOrElse(false))
}
