package diptestbed.web.control

import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.{catsSyntaxTuple2Semigroupal, toTraverseOps}
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.{DIPTestbedConfig, Hardware, HardwareId, User, UserId}
import diptestbed.web.control.FormHelper.optionalBoolean
import diptestbed.web.ioControls.IOController
import play.api.data.{Form, FormBinding, Mapping}
import play.api.data.Forms.{optional, text, tuple}
import play.api.i18n.Messages
import play.api.mvc._

import java.util.UUID
import scala.util.Try

class AppUserController(
  val appConfig: DIPTestbedConfig,
  val cc: ControllerComponents,
  val userService: UserService[IO],
  val hardwareService: HardwareService[IO]
)(implicit
  iort: IORuntime,
  messages: Messages
) extends AbstractController(cc)
    with IOController
    with ResultsController[IO]
    with AuthController[IO] {
  implicit val ac: DIPTestbedConfig = appConfig

  def setPermissions(
    userUUID: String,
    isManager: Boolean,
    isLabOwner: Boolean,
    isDeveloper: Boolean
  ): Boolean =
    Try(UUID.fromString(userUUID)).toOption.map(UserId)
      .traverse(id =>
        userService.setPermissions(id, isManager, isLabOwner, isDeveloper)
          .map(x => x.toOption.isDefined)).map(_.getOrElse(false)).unsafeRunSync()

  def setHardwareAccess(
    sessionUser: Option[User],
    userUUID: String,
    hardwareUUID: String,
    isAccessible: Boolean,
  ): Boolean =
    (Try(UUID.fromString(userUUID)).toOption.map(UserId),
      Try(UUID.fromString(hardwareUUID)).toOption.map(HardwareId)).tupled
      .traverse { case (userId, hardwareId) =>
        hardwareService.setHardwareAccess(sessionUser, userId, hardwareId, isAccessible)
          .map(x => x.toOption.isDefined) }.map(_.getOrElse(false)).unsafeRunSync()

  val permissionsForm: Form[(String, Boolean, Boolean, Boolean)] = Form[(String, Boolean, Boolean, Boolean)](
    tuple(
      "user_id" -> text,
      "is_manager" -> optionalBoolean,
      "is_lab_owner" -> optionalBoolean,
      "is_developer" -> optionalBoolean,
    ) verifying ("Failed to change permissions", {
      case (userId, isManager, isLabOwner, isDeveloper) =>
        setPermissions(userId, isManager, isLabOwner, isDeveloper)
    })
  )

  def hardwareAccessForm(sessionUser: User): Form[(String, String, Boolean)] = Form[(String, String, Boolean)](
    tuple(
      "user_id" -> text,
      "hardware_id" -> text,
      "is_accessible" -> optionalBoolean,
    ) verifying ("Failed to change user hardware access", {
      case (userId, hardwareId, accessible) =>
        setHardwareAccess(Some(sessionUser), userId, hardwareId, accessible)
    })
  )

  def dbUsers(requester: User): IO[List[User]] = userService.getUsers(Some(requester))
    .map(_.toOption.sequence.flatten.toList.filter(_ => requester.isManager))

  def dbUser(requester: User, user: UserId): IO[Option[User]] = userService.getUser(Some(requester), user)
    .map(_.toOption.sequence.flatten.filter(_ => requester.isManager))

  def dbAccessibleHardware(requester: User, accessUser: UserId): IO[List[(Hardware, Boolean)]] =
    hardwareService.getManageableHardware(Some(requester), accessUser)
      .map(_.toOption.sequence.flatten.toList.filter(_ => requester.isManager))

  def list: Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, user) =>
        Ok(diptestbed.web.views.html.userList(
          appConfig, Some(user), dbUsers(user).unsafeRunSync(), permissionsForm))
      }.unsafeRunSync()
    }

  def view(userId: UserId): Action[AnyContent] =
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, sessionUser) =>
        dbUser(sessionUser, userId).unsafeRunSync() match {
          case None => Redirect(appConfig.withAppPath("/user"))
          case Some(user) =>
            if (sessionUser.isManager || sessionUser.isLabOwner)
              Ok(diptestbed.web.views.html.user(
                appConfig, Some(sessionUser), user, permissionsForm, dbAccessibleHardware(sessionUser, userId).unsafeRunSync(), hardwareAccessForm(sessionUser)))
            else Redirect(appConfig.withAppPath("/user"))
        }
      }.unsafeRunSync()
    }

  def permissionsRequest(userId: Option[UserId]): Action[AnyContent] = {
    def badResult[A](sessionUser: User, form: Form[(String, Boolean, Boolean, Boolean)])(implicit r: Request[A]) = {
      userId match {
        case None =>
          BadRequest(diptestbed.web.views.html.userList(
            appConfig, Some(sessionUser), dbUsers(sessionUser).unsafeRunSync(), form))
        case Some(userId) =>
          dbUser(sessionUser, userId).unsafeRunSync() match {
            case None => Redirect(appConfig.withAppPath(s"/user/${userId}"))
            case Some(user) =>
              BadRequest(diptestbed.web.views.html.user(
                appConfig, Some(sessionUser), user, form, dbAccessibleHardware(sessionUser, userId).unsafeRunSync(), hardwareAccessForm(sessionUser)))
          }
      }
    }
    Action { implicit request =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, sessionUser) =>
        if (!sessionUser.isManager) {
          val formWithManagerError = permissionsForm.withGlobalError("Manager permission required")
          badResult(sessionUser, formWithManagerError)
        } else {
          permissionsForm.bindFromRequest.fold(
            formWithErrors => badResult(sessionUser, formWithErrors),
            _ => userId match {
              case None => Redirect(appConfig.withAppPath(s"/user"))
              case Some(id) => Redirect(appConfig.withAppPath(s"/user/${id.value}"))
            }
          )
        }
      }.unsafeRunSync()
    }
  }

  def hardwareAccessRequest(userId: UserId): Action[AnyContent] = {
    def badResult[A](sessionUser: User, form: Form[(String, String, Boolean)])(implicit r: Request[A]): Result =
      dbUser(sessionUser, userId).unsafeRunSync() match {
        case None => Redirect(appConfig.withAppPath(s"/user/${userId.value}"))
        case Some(user) =>
          BadRequest(diptestbed.web.views.html.user(
            appConfig, Some(sessionUser), user, permissionsForm, dbAccessibleHardware(sessionUser, userId).unsafeRunSync(), form))
      }

    Action { implicit request: Request[AnyContent] =>
      withRequestAuthnOrLoginRedirect[AnyContent] { case (_, sessionUser) =>
        if (!sessionUser.isManager && !sessionUser.isLabOwner) {
          val formWithManagerError = hardwareAccessForm(sessionUser).withGlobalError("Hardware access permission required")
          badResult(sessionUser, formWithManagerError)
        } else {
          hardwareAccessForm(sessionUser).bindFromRequest().fold(
            formWithErrors => badResult(sessionUser, formWithErrors),
            _ => Redirect(appConfig.withAppPath(s"/user/${userId.value}"))
          )
        }
      }.unsafeRunSync()
    }
  }


}
