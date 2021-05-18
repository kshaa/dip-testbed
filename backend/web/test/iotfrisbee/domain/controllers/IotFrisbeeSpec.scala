package iotfrisbee.domain.controllers

import akka.util.Timeout
import cats.effect.testing.scalatest.AsyncIOSpec
import iotfrisbee.web.IotFrisbeeModule
import org.scalatest.TestSuite
import org.scalatest.freespec.AsyncFreeSpecLike
import org.scalatest.matchers.should.Matchers
import org.scalatestplus.play.components.WithApplicationComponents
import play.api.{BuiltInComponents, Configuration}
import scala.concurrent.duration.DurationInt

trait IotFrisbeeSpec
    extends TestSuite
    with AsyncFreeSpecLike
    with AsyncIOSpec
    with Matchers
    with WithApplicationComponents {
  implicit def defaultAwaitTimeout: Timeout = 60.seconds
  override def components: BuiltInComponents = null
  val testSuiteName: String = this.getClass.getSimpleName.toLowerCase()
  def module(testName: String = testSuiteName): IotFrisbeeModule =
    new IotFrisbeeModule(
      context.copy(initialConfiguration =
        Configuration(
          "iotfrisbee.test.enabled" -> true,
          "iotfrisbee.test.name" -> testName,
        ).withFallback(context.initialConfiguration),
      ),
    )
}
