package diptestbed.web.config

import diptestbed.domain.{DIPTestbedConfig => DomainDIPTestbedConfig, TestConfig => DomainTestConfig}
import diptestbed.web.config.TestConfig._
import com.typesafe.config.Config
import play.api.{ConfigLoader, Configuration}

object DIPTestbedConfig {
  implicit val dipTestbedConfigLoader: ConfigLoader[DomainDIPTestbedConfig] = (rootConfig: Config, path: String) => {
    val config: Configuration = Configuration(rootConfig.getConfig(path))

    DomainDIPTestbedConfig.fromConfig(
      testConfig = config.get[DomainTestConfig]("test"),
      clusterized = config.getOptional[Boolean]("clusterized"),
    )
  }
}