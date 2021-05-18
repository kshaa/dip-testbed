package iotfrisbee.web

import play.api._
import play.api.ApplicationLoader.Context
import cats.effect.unsafe.implicits.global

class IotFrisbeeLoader extends ApplicationLoader {
  def load(context: Context): Application = {
    LoggerConfigurator(context.environment.classLoader)
      .foreach(
        _.configure(
          context.environment,
          context.initialConfiguration,
          Map.empty,
        ),
      )

    val iotFrisbeeModule = new IotFrisbeeModule(context)
    iotFrisbeeModule.applicationEvolutions
    iotFrisbeeModule.application
  }
}
