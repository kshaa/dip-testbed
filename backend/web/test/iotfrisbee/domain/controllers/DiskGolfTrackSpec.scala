package iotfrisbee.domain.controllers

import org.scalatest._
import play.api.mvc.AnyContent
import akka.stream.Materializer
import akka.util.Timeout
import cats.effect.IO
import cats.implicits._
import io.circe._
import io.circe.syntax.EncoderOps
import iotfrisbee.domain.controllers.DiskGolfTrackSpec._
import iotfrisbee.domain.{DiskGolfTrack, DiskGolfTrackId, DomainTimeZoneId}
import iotfrisbee.domain.controllers.IotFrisbeeSpec.exchangeJSON
import iotfrisbee.domain.controllers.UserControllerSpec._
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.IotFrisbeeModule
import iotfrisbee.web.controllers.{DiskGolfTrackController, UserController}

class DiskGolfTrackSpec extends IotFrisbeeSpec with GivenWhenThen {
  lazy val module: IotFrisbeeModule = module()
  implicit lazy val materializer: Materializer = module.materializer
  lazy val userController: UserController = module.userController
  lazy val diskGolfTrackController: DiskGolfTrackController = module.diskGolfTrackController

  "DiskGolfTrackController" - {
    "should be valid" in {
      for {
        _ <- IO.pure(Given("An empty database"))

        _ = When("A user w/ a generated is created")
        userCreation <- createUser(userController, CreateUser("janisberzins"))
        user = userCreation.map(_.value).toOption.get

        _ = Then("A disk golf track w/ a generated id should be creatable")
        rigaTimeZoneId = DomainTimeZoneId.fromString("Europe/Riga").toOption.get
        diskGolfTrackCreation <- createDiskGolfTrack(
          diskGolfTrackController,
          CreateDiskGolfTrack(user.id, "Talsi", rigaTimeZoneId),
        )
        diskGolfTrack = diskGolfTrackCreation.map(_.value).toOption
        diskGolfTrackCheck =
          diskGolfTrackCreation
            .map(t => (t.value.name, t.value.timezoneId))
            .shouldEqual(Right("Talsi", rigaTimeZoneId))

        _ = Then("A disk golf track should be retrievable by a generated id")
        diskGolfTrackGet <-
          diskGolfTrack.traverse(t => getDiskGolfTrack(diskGolfTrackController, t.id).map(_.toOption)).map(_.flatten)
        diskGolfTrackGetCheck = diskGolfTrackGet.map(_.value.name).shouldEqual(Some("Talsi"))

        _ = And("A disk golf track should be listed")
        diskGolfTrackListing <- getDiskGolfTracks(diskGolfTrackController)
        diskGolfTrackListingCheck = diskGolfTrackListing.map(_.value.map(_.name)).shouldEqual(Right("Talsi" :: Nil))

        assertions = diskGolfTrackCheck :: diskGolfTrackGetCheck :: diskGolfTrackListingCheck :: Nil
        assertion = assertions.forall(_ === Succeeded).shouldBe(true)
      } yield assertion
    }
  }
}

object DiskGolfTrackSpec {
  def createDiskGolfTrack(
    diskGolfTrackController: DiskGolfTrackController,
    createDiskGolfTrack: CreateDiskGolfTrack,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[DiskGolfTrack]]] =
    exchangeJSON[CreateDiskGolfTrack, Success[DiskGolfTrack]](
      diskGolfTrackController.createDiskGolfTrack,
      Some(createDiskGolfTrack.asJson),
    )

  def getDiskGolfTracks(
    diskGolfTrackController: DiskGolfTrackController,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[List[DiskGolfTrack]]]] =
    exchangeJSON[AnyContent, Success[List[DiskGolfTrack]]](diskGolfTrackController.getDiskGolfTracks, None)

  def getDiskGolfTrack(
    diskGolfTrackController: DiskGolfTrackController,
    diskGolfTrackId: DiskGolfTrackId,
  )(implicit timeout: Timeout, materializer: Materializer): IO[Either[Error, Success[DiskGolfTrack]]] =
    exchangeJSON[AnyContent, Success[DiskGolfTrack]](diskGolfTrackController.getDiskGolfTrack(diskGolfTrackId), None)
}
