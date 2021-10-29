package diptestbed.domain

case class DIPTestbedConfig(testConfig: TestConfig, clusterized: Boolean)
object DIPTestbedConfig {
  def fromConfig(testConfig: TestConfig, clusterized: Option[Boolean]): DIPTestbedConfig =
    DIPTestbedConfig(testConfig, clusterized.getOrElse(false))
}
