package diptestbed.web.config

import diptestbed.domain.{DIPTestbedConfig => DomainDIPTestbedConfig, TestConfig => DomainTestConfig}
import diptestbed.web.config.TestConfig._
import com.typesafe.config.Config
import play.api.{ConfigLoader, Configuration}

object DIPTestbedConfig {
  implicit val dipTestbedConfigLoader: ConfigLoader[DomainDIPTestbedConfig] = (rootConfig: Config, path: String) => {
    val config: Configuration = Configuration(rootConfig.getConfig(path))

    DomainDIPTestbedConfig.fromConfig(
      config.get[DomainTestConfig]("test"),
      config.getOptional[Boolean]("clusterized"),
      config.get[String]("title"),
      config.get[String]("basePath")
    )
  }
}
