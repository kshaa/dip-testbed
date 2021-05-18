package iotfrisbee.web.configloaders

import iotfrisbee.domain.{IotFrisbeeConfig => DomainIotFrisbeeConfig, TestConfig => DomainTestConfig}
import iotfrisbee.web.configloaders.TestConfig._
import com.typesafe.config.Config
import play.api.{ConfigLoader, Configuration}

object IotFrisbeeConfig {
  implicit val iotFrisbeeConfigLoader: ConfigLoader[DomainIotFrisbeeConfig] = (rootConfig: Config, path: String) => {
    val config: Configuration = Configuration(rootConfig.getConfig(path))

    DomainIotFrisbeeConfig(
      testConfig = config.get[DomainTestConfig]("test"),
    )
  }
}
