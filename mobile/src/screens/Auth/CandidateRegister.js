import React, { useState } from "react";
import { Image, ScrollView, Text, TouchableOpacity, View } from "react-native";
import { Button, HelperText, TextInput } from "react-native-paper";
import styles from "../../styles/Auth/CandidateRegisterStyles"; // Style của JobLink
import Apis, { endpoints } from "../../utils/Apis";
import { Alert } from "react-native";
const CandidateRegister = ({ navigation }) => {
  // 1. Cấu hình mảng Fields (Format thầy giáo)
  const info = [
    {
      title: "Full Name",
      field: "first_name", // Gộp tên vào đây
      icon: "account-outline"
    },

    {
      title: "Email",
      field: "email",
      icon: "email-outline"
    },
    {
      title: "Password",
      field: "password",
      icon: "lock-outline",
      secure: true
    },
    {
      title: "Confirm Password",
      field: "confirm",
      icon: "lock-check-outline",
      secure: true
    }
  ];

  // 2. State quản lý
  const [user, setUser] = useState({});
  const [err, setErr] = useState(false);
  const [loading, setLoading] = useState(false);
  // State quản lý ẩn/hiện mật khẩu (mở rộng thêm để UX tốt hơn)
  const [showPass, setShowPass] = useState({});

  // 4. Validate
  const validate = () => {
    if (!user.password || user.password !== user.confirm) {
      setErr(true);
      return false;
    }
    setErr(false);
    return true;
  }

  // 5. Hàm Đăng ký (Logic Loop FormData chuẩn thầy)
  const register = async () => {
    if (validate() === true) {
      try {
        setLoading(true);
        let form = new FormData();
        for (let key in user)
          if (key !== 'confirm') {
            form.append(key, user[key]);
          }

        console.info("Sending Data:", user);
        console.log(form)
        let res = await Apis.post(endpoints['register_candidate'], form, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        if (res.status === 201) {
          console.log("Đăng ký thành công:", res.data);
          navigation.navigate("Login");
        }

      } catch (ex) {
        let message = "Đăng ký thất bại.";

        if (ex.response && ex.response.data) {
          const errorData = ex.response.data;
          console.log("Lỗi Server:", errorData);

          // --- TỪ ĐIỂN DỊCH THUẬT (Frontend Map) ---
          const fieldMap = {
            "email": "Email",
            "username": "Tên đăng nhập",
            "password": "Mật khẩu",
            "first_name": "Tên",
            "last_name": "Họ",
            "phone": "Số điện thoại",
            "non_field_errors": "Lỗi chung"
          };
          // -------------------------------------------

          if (typeof errorData === 'object') {
            message = "";
            for (let key in errorData) {
              // 1. Dịch tên trường (VD: email -> Email)
              let vnField = fieldMap[key] || key;

              let errContent = errorData[key];
              if (Array.isArray(errContent)) errContent = errContent[0]; // Lấy lỗi đầu tiên

              // 3. Dịch nội dung lỗi (VD: This field is required -> Không được bỏ trống)
              // Chuyển về chữ thường để so sánh cho dễ
              let lowerContent = String(errContent).toLowerCase();

              // Tìm trong từ điển, nếu không thấy thì dùng tạm tiếng Anh
              let vnMessage = "";

              // Logic tìm kiếm thông minh (Check xem có chứa từ khóa không)
              if (lowerContent.includes("already exists")) {
                vnMessage = "đã tồn tại trong hệ thống.";
              } else if (lowerContent.includes("required")) {
                vnMessage = "là bắt buộc.";
              } else
                vnMessage = "không hợp lệ.";
              message += `• ${vnField} ${vnMessage}\n`;
            }
          }
        } else {
          message = "Lỗi kết nối hoặc Server không phản hồi.";
        }

        Alert.alert("Thông báo", message);
      } finally {
        setLoading(false);
      }
    }
  }

  // Hàm phụ trợ để toggle password
  const toggleShow = (field) => {
    setShowPass(prev => ({ ...prev, [field]: !prev[field] }));
  }

  return (
    <View style={styles.container}>
      {/* Header JobLink */}
      <View style={styles.headerContainer}>
        <Text style={styles.appName}>Job<Text style={styles.brandHighlight}>Link</Text></Text>
        <Text style={styles.tagline}>Create a candidate account 🚀</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        <HelperText type="error" visible={err}>
          Mật khẩu KHÔNG khớp!
        </HelperText>
        {/* --- VÒNG LẶP RENDER INPUT (Format thầy) --- */}
        {info.map(i => {
          const isErrorField = err && (i.field === 'password' || i.field === 'confirm');
          return (

            <TextInput
              key={i.field}
              style={styles.input}
              value={user[i.field]}
              onChangeText={(t) => {
                setUser({ ...user, [i.field]: t });
                if (err) setErr(false); // Tự động tắt lỗi khi người dùng nhập lại
              }}
              label={i.title}
              mode="outlined"

              // React Native Paper hỗ trợ prop 'error' để tô đỏ tự động
              error={isErrorField}

              // Màu viền khi active (nếu không lỗi thì màu tím, nếu lỗi thì Paper tự xử lý màu đỏ)
              activeOutlineColor={isErrorField ? "red" : "#130160"}
              outlineColor="#EAEAEA"

              theme={{ roundness: 10 }}
              secureTextEntry={i.secure ? !showPass[i.field] : false}
              left={<TextInput.Icon icon={i.icon} color={isErrorField ? "red" : "#AAA6B9"} />}
              right={
                i.secure ?
                  <TextInput.Icon
                    icon={showPass[i.field] ? "eye-off" : "eye"}
                    onPress={() => toggleShow(i.field)}
                    color={isErrorField ? "red" : "#AAA6B9"}
                  /> : null
              }
            />
          )
        })}

        {/* Nút Đăng ký */}
        <Button
          loading={loading}
          disabled={loading}
          style={styles.registerBtn}
          labelStyle={styles.registerBtnLabel}
          icon="account-plus"
          mode="contained"
          onPress={register}
        >
          SIGN UP
        </Button>

        {/* Footer chuyển hướng */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account?</Text>
          <TouchableOpacity onPress={() => navigation.reset({
            index: 0,
            routes: [{ name: 'Login' }],
          })}>
            <Text style={styles.loginText}>Log in</Text>
          </TouchableOpacity>
        </View>

        {/* Link sang Employer */}
        <View style={{ marginTop: 10, alignItems: 'center', marginBottom: 30 }}>
          <Text style={{ color: '#95969D', marginBottom: 10 }}>Looking to hire talent?</Text>
          <Button
            mode="outlined"
            textColor="#130160"
            style={{ borderColor: '#130160', width: '100%' }}
            onPress={() => navigation.navigate('EmployerRegister')}
          >
            Create Employer Account
          </Button>
        </View>

      </ScrollView>
    </View>
  );
}

export default CandidateRegister;